class TriggerTimes:
    MangaUpdate: str = "5 3 * * *"
    DeliveryReady: str = "28 * * * *"  # Every hour at 28 minutes
    ReturnTracker: str = "35 * * * *"  # Every hour at 35 minutes
    WinSim: str = "0 21 * * *"  # Every day at 21:00
    Mietplan: str = "1 21 * * *"  # Every day at 21:01
    MailCheck: str = "*/5 * * * *"  # Every 5 minutes
