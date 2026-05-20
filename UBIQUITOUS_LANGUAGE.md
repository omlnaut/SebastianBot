# Ubiquitous Language

## Task Management

| Term         | Definition                                                                 | Aliases to avoid |
| ------------ | -------------------------------------------------------------------------- | ---------------- |
| **Task**     | An actionable item that needs to be completed, often with a due date.      | Todo, item       |
| **TaskList** | A container used to group related **Tasks** (e.g., Mangas, Bibo).          | Category, group  |
| **Label**    | A tag applied to a **Task** to indicate its source or specific processing. | Tag, flag        |

## Library (Bibo)

| Term            | Definition                                                                  | Aliases to avoid |
| --------------- | --------------------------------------------------------------------------- | ---------------- |
| **Lending**     | A record of a borrowed book including its title and return deadline.        | Loan, book, item |
| **Bibo Account**| A specific set of credentials for a library user (e.g., Oli, Katja).        | User, login      |
| **Sync Tag**    | A unique identifier in a **Calendar Event** description to track a lending. | Sync ID          |

## Media & Entertainment

| Term          | Definition                                                            | Aliases to avoid  |
| ------------- | --------------------------------------------------------------------- | ----------------- |
| **Manga**     | A specific comic series being tracked for new releases.               | Series, book      |
| **Chapter**   | A single installment or update of a **Manga**.                        | Episode, release  |
| **Publisher** | An entity that releases **Mangas** (e.g., FlameComics, MangaPlus).    | Source, group     |

## Logistics (Delivery)

| Term            | Definition                                                              | Aliases to avoid |
| --------------- | ----------------------------------------------------------------------- | ---------------- |
| **Pickup Data** | Information extracted from a delivery notification (item, location, due date). | Package info     |
| **Delivery Mail**| An automated email from a carrier indicating a package is ready for collection. | Notification     |

## System & Actions

| Term            | Definition                                                                  | Aliases to avoid  |
| --------------- | --------------------------------------------------------------------------- | ----------------- |
| **Side Effect** | An external action performed by the system (e.g., creating a task, sending a message). | Event, action, result |
| **UseCase**     | A specific business logic flow that processes input and produces **Side Effects**. | Service, feature  |

## Relationships

- A **TaskList** contains multiple **Tasks**.
- A **Lending** belongs to one **Bibo Account**.
- A **Lending** is synchronized as a **Calendar Event** using a **Sync Tag**.
- A **Manga** has multiple **Chapters**.
- A **Delivery Mail** is parsed into **Pickup Data**, which creates a **Task**.

## Example dialogue

> **Dev:** "How does the system know which **Lending** has already been added to the calendar?"
> **Domain expert:** "We check the **Calendar Event** for a specific **Sync Tag**. If the **Sync Tag** matches the **Lending** ID and the **Bibo Account**, we just update the date if it changed."
> **Dev:** "And if the book is returned?"
> **Domain expert:** "The **Lending** will disappear from the library. The next time the **UseCase** runs, it won't find the **Lending**, so it generates a **Side Effect** to delete the **Calendar Event**."
> **Dev:** "Does every **Delivery Mail** result in a **Task**?"
> **Domain expert:** "Yes, we parse the **Pickup Data** from the HTML and create a **Task** in the 'Default' **TaskList** with a 'DELIVERY_READY' **Label**."

## Flagged ambiguities

- **Event**: Used for both **Calendar Event** (a domain entity in a user's calendar) and **Side Effect** (internal system events like `BaseActorEvent`). Recommendation: Use "Event" specifically for Calendar entries and "Side Effect" for system outputs.
- **Account**: Used for **Bibo Account** (library login). Should not be confused with authentication accounts or cloud service accounts.
- **Label**: Used specifically for **Task** categorization in the system, distinct from Gmail labels (though `ModifyMailLabel` exists).
