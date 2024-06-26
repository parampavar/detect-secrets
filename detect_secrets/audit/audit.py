"""
The audit module allows analysts to easily scan the baseline, and verify whether
the secrets flagged are actually secrets.
"""
from . import io
from ..core import baseline
from ..exceptions import NoLineNumberError
from ..exceptions import SecretNotFoundOnSpecifiedLineError
from ..types import SecretContext
from ..util.code_snippet import get_code_snippet
from .common import get_baseline_from_file
from .common import get_raw_secret_from_file
from .common import open_file
from .iterator import BidirectionalIterator
from .iterator import get_secret_iterator


def audit_baseline(filename: str) -> None:
    """
    :raises: InvalidBaselineError
    """
    secrets = get_baseline_from_file(filename)

    secrets.trim()
    if _classify_secrets(get_secret_iterator(secrets)):
        io.print_message('Saving progress...')
        baseline.save_to_file(secrets, filename)


def _classify_secrets(iterator: BidirectionalIterator) -> bool:
    """
    :returns: True if changes were made.
    """
    # NOTE: Technically, this is a conservative estimate. If an entry was changed to the same
    # value, we would return True as well.
    has_changes = False

    for secret in iterator:
        try:
            secret.secret_value = get_raw_secret_from_file(secret)
            io.clear_screen()
            io.print_context(
                SecretContext(
                    current_index=iterator.index + 1,
                    num_total_secrets=len(iterator.collection),
                    secret=secret,
                    snippet=get_code_snippet(
                        lines=open_file(secret.filename).raw_lines,
                        line_number=secret.line_number,
                    ),
                ),
            )

            decision = io.get_user_decision(can_step_back=iterator.can_step_back())
        except SecretNotFoundOnSpecifiedLineError as e:
            io.clear_screen()
            io.print_secret_not_found(
                SecretContext(
                    current_index=iterator.index + 1,
                    num_total_secrets=len(iterator.collection),
                    secret=secret,
                    error=e,
                ),
            )

            decision = io.get_user_decision(
                prompt_secret_decision=False,
                can_step_back=iterator.can_step_back(),
            )
        except NoLineNumberError as e:
            io.print_error(str(e))
            break

        if decision == io.InputOptions.QUIT:
            io.print_message('Quitting...')
            break

        if decision == io.InputOptions.BACK:
            iterator.step_back_on_next_iteration()

        # The question asked is: "Should this string be committed to the repository?"
        elif decision == io.InputOptions.NO:
            secret.is_secret = True
            has_changes = True
        elif decision == io.InputOptions.YES:
            secret.is_secret = False
            has_changes = True
        elif decision == io.InputOptions.SKIP and secret.is_secret is not None:
            # This handles the case of back-stepping to clear a mistake.
            # This is not triggered for pre-labelled secrets, as pre-labelled secrets will be
            # excluded from this iterator.
            secret.is_secret = None
            has_changes = True

    return has_changes
