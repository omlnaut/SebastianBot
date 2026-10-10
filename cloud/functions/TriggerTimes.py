class TriggerTimes:
    MangaUpdate: str = "5 3 * * *"
    DeliveryReady: str = "28 * * * *"  # Every hour at 28 minutes
    CheckParcelReceived: str = "43 * * * *"  # Every hour at 43 minutes
    SetMissingTaskDueDate: str = "0 * * * *"  # Every hour at minute 0
    ReturnTracker: str = "35 * * * *"  # Every hour at 35 minutes
    WinSim: str = "0 21 * * *"  # Every day at 21:00
    Mietplan: str = "1 21 * * *"  # Every day at 21:01
    MailCheck: str = "*/10 * * * *"  # Every 10 minutes
    BiboLendingSync: str = "0 3 * * *"  # Every day at 03:00
    BiboLendingSyncWife: str = "5 3 * * *"  # Every day at 03:05
