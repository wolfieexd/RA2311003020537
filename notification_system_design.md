# Stage 1: REST API Design

## Notification System API Contract

The system uses a combination of REST APIs for CRUD operations and Server-Sent Events (SSE) for real-time notification delivery. SSE is chosen over WebSockets because notifications are inherently a one-way communication channel (server to client). SSE is lighter, runs over standard HTTP, and has built-in browser support for automatic reconnection.

### 1. Get All Notifications
**Method:** `GET`
**URL:** `/notifications`
**Headers:** `Authorization: Bearer <token>`
**Query Params:**
- `page` (integer, optional): Page number (default: 1)
- `limit` (integer, optional): Items per page (default: 20)
- `type` (string, optional): Filter by type (`Result`, `Placement`, `Event`)

**Response Schema (200 OK):**
```json
{
  "page": 1,
  "limit": 20,
  "total": 1500,
  "notifications": [
    {
      "id": "uuid-string",
      "type": "Result | Placement | Event",
      "message": "string",
      "timestamp": "2026-04-22T17:51:30Z",
      "isRead": false,
      "studentId": "string"
    }
  ]
}
```

### 2. Get Single Notification
**Method:** `GET`
**URL:** `/notifications/{id}`
**Headers:** `Authorization: Bearer <token>`

**Response Schema (200 OK):**
```json
{
  "id": "uuid-string",
  "type": "Placement",
  "message": "C5X Corporation hiring",
  "timestamp": "2026-04-22T17:51:18Z",
  "isRead": false,
  "studentId": "string"
}
```
**Error (404 Not Found):** `{"detail": "Notification not found"}`

### 3. Mark Single Notification as Read
**Method:** `PATCH`
**URL:** `/notifications/{id}/read`
**Headers:** `Authorization: Bearer <token>`

**Response Schema (200 OK):**
```json
{
  "id": "uuid-string",
  "isRead": true
}
```

### 4. Mark All Notifications as Read
**Method:** `PATCH`
**URL:** `/notifications/read-all`
**Headers:** `Authorization: Bearer <token>`

**Response Schema (200 OK):**
```json
{
  "updatedCount": 15,
  "message": "All notifications marked as read"
}
```

### 5. Get Unread Count
**Method:** `GET`
**URL:** `/notifications/unread/count`
**Headers:** `Authorization: Bearer <token>`

**Response Schema (200 OK):**
```json
{
  "unreadCount": 5
}
```

### 6. Real-Time Push Mechanism (SSE)
**Method:** `GET`
**URL:** `/notifications/stream`
**Headers:** `Authorization: Bearer <token>`, `Accept: text/event-stream`

**Response:** Continuous text stream where each event is a JSON-encoded notification.

---

# Stage 2: Persistent Storage Design

### 1. Which DB?
**Choice:** PostgreSQL (SQL).
**Justification:** The notification structure is uniform and highly structured. We require indexing for filtering (by `studentId`, `isRead`, `type`), sorting by `timestamp`, and potentially complex aggregations (e.g., getting counts of certain notification types). PostgreSQL handles these perfectly and supports JSON columns if minimal flexibility is needed. While a NoSQL DB like MongoDB is good for write-heavy unstructured data, a relational database like PostgreSQL provides excellent guarantees and indexing options for a read-heavy query like fetching unread notifications by ID. For millions of rows, partitioned tables on PostgreSQL work exceptionally well.

### 2. Full DB Schema

```sql
CREATE TYPE notification_type AS ENUM ('Result', 'Placement', 'Event');

CREATE TABLE students (
    student_id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL
);

CREATE TABLE notifications (
    id UUID PRIMARY KEY,
    student_id UUID NOT NULL REFERENCES students(student_id) ON DELETE CASCADE,
    type notification_type NOT NULL,
    message TEXT NOT NULL,
    is_read BOOLEAN DEFAULT FALSE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_notifications_student_id ON notifications(student_id);
CREATE INDEX idx_notifications_created_at ON notifications(created_at DESC);
CREATE INDEX idx_notifications_is_read ON notifications(is_read);
```

### 3. Scaling Problems at 50,000 Students × Millions of Notifications
- **Table Size:** A single table will grow into hundreds of millions of rows, slowing down writes (index updates) and reads.
- **Query Performance:** Unread count queries and pagination over large result sets will start doing table scans if not properly indexed.
- **Read/Write Contention:** Mass writes (e.g., notifying all 50k students) will lock rows/indexes and block incoming read requests.

### 4. Solutions
- **Partitioning:** Partition the `notifications` table by `created_at` (e.g., monthly partitions) to keep index sizes small and allow fast pruning of old data.
- **Archival:** Move notifications older than 6 months to cold storage.
- **Read Replicas:** Route `GET` requests to read replicas to offload the primary write DB during bulk notifications.

### 5. Queries for Stage 1 Endpoints
```sql
-- Get All (Paginated)
SELECT * FROM notifications 
WHERE student_id = '...' 
ORDER BY created_at DESC LIMIT 20 OFFSET 0;

-- Get Unread Count
SELECT COUNT(*) FROM notifications 
WHERE student_id = '...' AND is_read = FALSE;

-- Mark as Read
UPDATE notifications SET is_read = TRUE 
WHERE id = '...' AND student_id = '...';
```

---

# Stage 3: Query Analysis & Optimization

### 1. Is this query accurate? What's wrong with it?
`SELECT * FROM notifications WHERE studentID = 1042 AND isRead = false ORDER BY createdAt DESC;`
Yes, it's logically accurate for finding unread notifications. However, it's slow because if there are millions of rows, the database must scan rows matching the studentID, filter by isRead, and then sort by createdAt. Without a composite index, this is extremely inefficient.

### 2. Why is it slow?
If there is no index covering `(studentID, isRead, createdAt)`, the database will perform an index scan on `studentID`, then fetch the rows to filter by `isRead`, and finally perform an in-memory sort on `createdAt` before returning. This "filesort" or full heap fetch is expensive.

### 3. Optimized Query
The query itself is fine, but it needs an index to be fast:
`CREATE INDEX idx_student_unread_recent ON notifications (studentID, isRead, createdAt DESC);`
With this composite index, the database can directly read the index and return the rows already sorted.

### 4. Computation Cost Before vs After
- **Before:** O(N) where N is the number of notifications for the student (fetching all from heap, sorting them).
- **After:** O(log M + K) where M is the total rows in the index, and K is the number of results returned (simply traversing the B-Tree index). 

### 5. Add indexes on every column?
**Bad advice.**
- **Tradeoffs:** Every index slows down `INSERT`, `UPDATE`, and `DELETE` operations because the index must be updated alongside the row. They also consume disk space and memory (RAM). Only index columns used in `WHERE`, `ORDER BY`, or `JOIN` clauses.

### 6. Query: Placement notifications in last 7 days
```sql
SELECT DISTINCT studentID 
FROM notifications 
WHERE type = 'Placement' 
AND createdAt >= NOW() - INTERVAL '7 days';
```

---

# Stage 4: Performance & Caching

### 1. Solutions
- **Redis Caching:** Cache the unread count and the first page of notifications.
- **Pagination / Infinite Scroll:** Fetch data in small chunks (e.g., 20 items).
- **Background Jobs:** Offload heavy unread count calculations or cache warming to background workers.

### 2. Implementation
- **Redis:** On notification insert, increment a Redis key `unread:student_id`. On read, fetch from Redis instead of SQL. If cache miss, calculate from SQL and set Redis key.
- **Pagination:** Implement keyset pagination (`WHERE id < last_id`) instead of `OFFSET` to avoid scanning rows.

### 3. Tradeoffs
- **Redis Cache:** High speed, but requires handling cache invalidation (stale data if SQL and Redis go out of sync). Adds infrastructure complexity.
- **Keyset Pagination:** Extremely fast, but users cannot jump to specific pages (e.g., "Page 10"), they can only go "Next".

### 4. Recommendation
A combination of **Keyset Pagination** for the notification feed and **Redis caching** for the `unread count`. The unread count is the most frequently requested data (on every page load of the app), making Redis ideal for it. Keyset pagination ensures infinite scrolling remains fast regardless of feed size.

---

# Stage 5: Bulk Notification Reliability

### 1. Shortcomings of the proposed implementation
- **Synchronous execution:** Blocking the request thread. If each email takes 1 second, 50,000 emails will take 14 hours!
- **Lack of transactional integrity:** If `send_email` fails on student 201, the loop breaks. Students 201-50,000 get nothing.
- **No retries:** Temporary network failures in the Email API will cause silent permanent failures.

### 2. What happened to the 200 students?
Since `send_email` failed and presumably threw an exception, the execution stopped for that student. They didn't get a DB record or an in-app notification because those lines come after `send_email`. The remaining 49,800 students were never processed.

### 3. Should saving to DB and sending email be atomic?
They cannot be strictly atomic because `send_email` is a network call to an external service. You can't "rollback" an email. Instead, you should use **Eventual Consistency** (e.g., Outbox Pattern) where you save to the DB first, and then asynchronously process the email.

### 4. Redesign for reliability and speed at scale
Use a Message Queue (e.g., RabbitMQ, Kafka) and asynchronous workers (e.g., Celery). 
- The API instantly returns 200 OK.
- A background job splits the 50,000 students into batches and pushes 50,000 messages to a queue.
- Worker nodes consume the queue, handle DB inserts, send emails, and push real-time events. If an email fails, the message is retried later.

### 5. Revised Pseudocode
```python
# API Endpoint
function notify_all_api(student_ids: array, message: string):
    batch_id = generate_uuid()
    publish_to_queue("bulk_notify", {batch_id, student_ids, message})
    return "Notification processing started"

# Background Worker (consuming 'bulk_notify' queue)
function process_bulk_notify(job):
    for student_id in job.student_ids:
        publish_to_queue("single_notify", {student_id, job.message})

# Background Worker (consuming 'single_notify' queue)
function process_single_notify(job, retry_count=0):
    try:
        # DB insert first (idempotent operation)
        save_to_db(job.student_id, job.message)
        
        # Realtime push
        push_to_app(job.student_id, job.message)
        
        # External call last
        send_email(job.student_id, job.message)
    except EmailAPIError:
        if retry_count < 3:
            schedule_retry("single_notify", job, retry_count + 1, delay=exponential_backoff())
        else:
            send_to_dead_letter_queue(job)
```

---

# Stage 6: Priority Inbox
The priority inbox addresses the problem of students missing critical notifications (like Placements) in a sea of lesser events. Instead of a purely chronological feed, it ranks unread notifications by computing a priority score.
1. `Placement` gets highest weight (3), `Result` (2), `Event` (1).
2. Timestamp recency acts as a tie-breaker.
3. The algorithm uses a Min-Heap of size `n` to efficiently compute the top-n items in `O(m log n)` time without sorting the entire dataset of size `m`.
