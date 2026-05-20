# Ubiquitous Language

## Task Management

| Term         | Definition                                                                  | Aliases to avoid |
| ------------ | --------------------------------------------------------------------------- | ---------------- |
| **Task**     | An actionable item that needs to be completed, often with a due date.       | Todo, item       |
| **TaskList** | A container used to group related **Tasks** (e.g., Mangas, Bibo).           | Category, group  |
| **Task Tag** | A tag applied to a **Task** to indicate its source or specific processing.  | Label, flag      |

## Library (Bibo)

| Term             | Definition                                                                  | Aliases to avoid |
| ---------------- | --------------------------------------------------------------------------- | ---------------- |
| **Lending**      | A record of a borrowed book including its title and return deadline.        | Loan, book, info |
| **Bibo Account** | A specific set of credentials for a library user (e.g., Oli, Katja).        | User, login      |
| **Sync Tag**     | A unique identifier in a **Calendar Event** description to track a lending. | Sync ID          |

## Logistics

| Term                      | Definition                                                                      | Aliases to avoid        |
| ------------------------- | ------------------------------------------------------------------------------- | ----------------------- |
| **Delivery Notification** | An automated email indicating a package is ready for collection at a point.     | Delivery Mail           |
| **Pickup Data**           | Information extracted from a **Delivery Notification** (item, location, date).  | Package info            |
| **Return Data**           | Information extracted from an Amazon return confirmation email.                 |                         |
| **Tracking Number**       | The unique identifier used by a carrier to track a parcel.                      | Tracking ID             |

## Mietplan

| Term                 | Definition                                                                    | Aliases to avoid |
| -------------------- | ----------------------------------------------------------------------------- | ---------------- |
| **Mietplan Folder**  | A virtual directory in the Mietplan system containing rental-related files.   | Folder           |
| **Mietplan File**    | A document (usually a PDF) found within a **Mietplan Folder**.               | File             |

## System & Actions

| Term                   | Definition                                                                         | Aliases to avoid  |
| ---------------------- | ---------------------------------------------------------------------------------- | ----------------- |
| **Side Effect**        | An external action performed by the system as a result of a **UseCase**.           | Event, action     |
| **UseCase**            | A specific business logic flow that processes input and produces **Side Effects**.  | Service, feature  |
| **Task Creation**      | A **Side Effect** that adds a new **Task** to a **TaskList**.                     |                   |
| **Task Completion**    | A **Side Effect** that marks an existing **Task** as finished.                     |                   |
| **Calendar Update**    | A **Side Effect** that creates, modifies, or deletes a **Calendar Event**.         |                   |
| **Message Dispatch**   | A **Side Effect** that sends a notification (e.g., via Telegram).                  |                   |
| **Mail Modification**  | A **Side Effect** that changes the state of an email (e.g., marking as read).      |                   |

## Relationships

- A **TaskList** contains multiple **Tasks**.
- A **Lending** belongs to one **Bibo Account**.
- A **Lending** is synchronized as a **Calendar Event** using a **Sync Tag**.
- A **Delivery Notification** is parsed into **Pickup Data**, which triggers **Task Creation**.
- **Tracking Number** is used to check if a parcel is ready to trigger **Task Completion**.

## Example dialogue

> **Dev:** "How do we handle a new package arrival?"
> **Domain expert:** "When a **Delivery Notification** arrives, the system parses the **Pickup Data**, including the **Tracking Number**. It then produces a **Task Creation** **Side Effect** to add a **Task** to the 'Default' **TaskList**."
> **Dev:** "And how do we know when to mark that **Task** as done?"
> **Domain expert:** "The `CheckParcelReceived` **UseCase** looks for **Tasks** with the `DELIVERY_READY` **Task Tag**. It uses the **Tracking Number** in the notes to check the carrier status. If the parcel is retrieved, it triggers a **Task Completion** **Side Effect**."
> **Dev:** "What about the library sync?"
> **Domain expert:** "For each **Bibo Account**, we fetch the **Lendings**. If a **Lending** isn't in the calendar, we perform a **Calendar Update**. We use the **Sync Tag** to find existing entries."

## Flagged ambiguities

- **Event**: Resolved. **Calendar Event** refers to domain entities in a calendar, while **Side Effect** refers to system actions.
- **Account**: Resolved. Use **Bibo Account** to refer to library credentials.
- **Label**: Resolved. Renamed to **Task Tag** to avoid confusion with Gmail labels.
- **Folder/File**: Resolved. Use **Mietplan Folder/File** to distinguish from generic system or drive concepts.
- **ID vs Number**: Resolved. Standardized on **Tracking Number** for parcel identification.
