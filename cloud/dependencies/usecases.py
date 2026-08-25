from typing import Callable, Sequence

from sebastian.usecases.features import (
    bibo_lending_sync,
    check_parcel_received,
    delivery_ready,
    mail_check,
    manga_update,
    mietplan,
    return_tracker,
    winsim,
    ingredient_parser,
)
from sebastian.usecases.features.mail_check import MailRetryConfiguration
from sebastian.usecases.side_effects import (
    complete_task,
    create_calendar_event,
    create_task,
    delete_calendar_event,
    modify_calendar_event,
    modify_mail_labels,
    send_telegram_message,
)
from sebastian.usecases.usecase_handler import UseCaseHandler

from .clients import (
    resolve_deepseek_client,
    resolve_dhl_client,
    resolve_bibo_client,
    resolve_calendar_event_client,
    resolve_gmail_client,
    resolve_google_drive_client,
    resolve_google_task_client,
    resolve_mangaupdate_client,
    resolve_mietplan_client,
    resolve_telegram_client,
)


def resolve_mietplan(
    mietplan_client: mietplan.IMietplanClient | None = None,
    google_drive_client: mietplan.IGoogleDriveClient | None = None,
    gdrive_folder_id: str = "19gdVV_DMtdQU0xi7TgfKJCRRc4c7m0fd",
) -> UseCaseHandler[mietplan.Request]:
    return mietplan.Handler(
        mietplan_client=mietplan_client or resolve_mietplan_client(),
        google_drive_client=google_drive_client or resolve_google_drive_client(),
        gdrive_folder_id=gdrive_folder_id,
    )


def resolve_mangaupdate_service(
    mangaupdate_client: manga_update.MangaUpdateClient | None = None,
) -> UseCaseHandler[manga_update.Request]:
    return manga_update.Handler(
        client=mangaupdate_client or resolve_mangaupdate_client(),
    )


def resolve_delivery_ready(
    llm_client: delivery_ready.LLMClient | None = None,
    retry_configuration: MailRetryConfiguration | None = None,
) -> delivery_ready.Handler:
    return delivery_ready.Handler(
        llm_client=llm_client or resolve_deepseek_client(),
        retry_configuration=retry_configuration or MailRetryConfiguration(),
    )


def resolve_delivery_ready_mail_sub_usecase(
    retry_configuration: MailRetryConfiguration | None = None,
    llm_client_resolver: Callable[[], delivery_ready.LLMClient] | None = None,
) -> mail_check.MailSubUseCase:
    return delivery_ready.MailSubUseCase(
        retry_configuration=retry_configuration or MailRetryConfiguration(),
        llm_client_resolver=llm_client_resolver or resolve_deepseek_client,
    )


def resolve_return_tracker_mail_sub_usecase(
    retry_configuration: MailRetryConfiguration | None = None,
    llm_client_resolver: Callable[[], return_tracker.LLMClient] | None = None,
) -> mail_check.MailSubUseCase:
    return return_tracker.MailSubUseCase(
        retry_configuration=retry_configuration or MailRetryConfiguration(),
        llm_client_resolver=llm_client_resolver or resolve_deepseek_client,
    )


def resolve_check_parcel_received(
    task_client: check_parcel_received.TaskClient | None = None,
    dhl_client: check_parcel_received.DhlClient | None = None,
) -> UseCaseHandler[check_parcel_received.Request]:
    return check_parcel_received.Handler(
        task_client=task_client or resolve_google_task_client(),
        dhl_client=dhl_client or resolve_dhl_client(),
    )


def resolve_bibo_lending_sync(
    bibo_account: bibo_lending_sync.BiboAccounts,
    bibo_client: bibo_lending_sync.BiboClient | None = None,
    calendar_client: bibo_lending_sync.CalendarClient | None = None,
) -> UseCaseHandler[bibo_lending_sync.Request]:
    return bibo_lending_sync.Handler(
        bibo_client=bibo_client or resolve_bibo_client(bibo_account),
        calendar_client=calendar_client or resolve_calendar_event_client(),
        bibo_account=bibo_account,
    )


def resolve_winsim(
    gmail_client: winsim.GmailClient | None = None,
    drive_client: winsim.GoogleDriveClient | None = None,
    winsim_folder_id: str = "1VGX5Wt8D3huZm3vVemjI3C6zz6W38PJr",
) -> UseCaseHandler[winsim.Request]:
    return winsim.Handler(
        gmail_client=gmail_client or resolve_gmail_client(),
        drive_client=drive_client or resolve_google_drive_client(),
        winsim_folder_id=winsim_folder_id,
    )


def resolve_return_tracker(
    gmail_client: return_tracker.GmailClient | None = None,
    llm_client: return_tracker.LLMClient | None = None,
    retry_configuration: MailRetryConfiguration | None = None,
) -> UseCaseHandler[return_tracker.Request]:
    return return_tracker.Handler(
        gmail_client=gmail_client or resolve_gmail_client(),
        llm_client=llm_client or resolve_deepseek_client(),
        retry_configuration=retry_configuration or MailRetryConfiguration(),
    )


def resolve_mail_check(
    gmail_client: mail_check.GmailClient | None = None,
    sub_usecases: Sequence[mail_check.MailSubUseCase] | None = None,
) -> UseCaseHandler[mail_check.Request]:
    # Phase 1 ordering is owned here in the composition root.
    resolved_sub_usecases = tuple(
        sub_usecases
        or (
            resolve_delivery_ready_mail_sub_usecase(),
            resolve_return_tracker_mail_sub_usecase(),
        )
    )
    return mail_check.Handler(
        gmail_client=gmail_client or resolve_gmail_client(),
        sub_usecases=resolved_sub_usecases,
    )


def resolve_modify_mail_label(
    gmail_client: modify_mail_labels.GmailClient | None = None,
) -> modify_mail_labels.Handler:
    return modify_mail_labels.Handler(
        gmail_client=gmail_client or resolve_gmail_client()
    )


def resolve_complete_task(
    task_client: complete_task.TaskClient | None = None,
) -> UseCaseHandler[complete_task.Request]:
    return complete_task.Handler(
        task_client=task_client or resolve_google_task_client(),
    )


def resolve_create_task(
    task_client: create_task.TaskClient | None = None,
) -> UseCaseHandler[create_task.Request]:
    return create_task.Handler(
        task_client=task_client or resolve_google_task_client(),
    )


def resolve_create_calendar_event(
    calendar_event_client: create_calendar_event.CalendarEventClient | None = None,
) -> UseCaseHandler[create_calendar_event.Request]:
    return create_calendar_event.Handler(
        calendar_event_client=calendar_event_client or resolve_calendar_event_client(),
    )


def resolve_delete_calendar_event(
    calendar_event_client: delete_calendar_event.CalendarEventClient | None = None,
) -> UseCaseHandler[delete_calendar_event.Request]:
    return delete_calendar_event.Handler(
        calendar_event_client=calendar_event_client or resolve_calendar_event_client(),
    )


def resolve_modify_calendar_event(
    calendar_event_client: modify_calendar_event.CalendarEventClient | None = None,
) -> UseCaseHandler[modify_calendar_event.Request]:
    return modify_calendar_event.Handler(
        calendar_event_client=calendar_event_client or resolve_calendar_event_client(),
    )


def resolve_send_telegram_message(
    telegram_client: send_telegram_message.TelegramClient | None = None,
) -> UseCaseHandler[send_telegram_message.Request]:
    return send_telegram_message.Handler(
        telegram_client=telegram_client or resolve_telegram_client(),
    )


# todo: if another one of those direct-call usecases is added, we should probably introduce a generic handler base like for UseCaesHandler
def resolve_ingredient_parser(
    llm_client: ingredient_parser.LLMClient | None = None,
) -> ingredient_parser.Handler:
    return ingredient_parser.Handler(
        llm_client=llm_client or resolve_deepseek_client(),
    )
