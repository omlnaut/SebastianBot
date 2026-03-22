from sebastian.domain.task import TaskLists


def to_id(tasklist: TaskLists) -> str:
    match tasklist:
        case TaskLists.Default:
            return "MDY0Mzc2NjgyMDc4MTc0Nzg3Mjk6MDow"
        case TaskLists.Mangas:
            return "WFRzM0JfdkdTXzl4WHVHNw"
        case TaskLists.Bibo:
            return "dTJVTXhYZk1feDlXNlBFMA"
        case _:
            raise ValueError(f"No known tasklist id for: {tasklist}")
