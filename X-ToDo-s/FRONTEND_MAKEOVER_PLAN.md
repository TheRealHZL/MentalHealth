# 🎨 MindBridge Frontend Makeover - Kompletter Plan

## 📋 Projekt-Übersicht

**Ziel:** Komplettes Frontend-Redesign mit allen verfügbaren Backend-Features und moderner UI/UX

**Wichtige Änderung:** 
- ✅ "Benutzer" statt "benutzer" - App ist NICHT nur Therapie-Tool!
- ✅ Wochenplaner für alle Benutzer (mit/ohne Therapeuten)
- ✅ Dark Mode Support (Hell/Dunkel/System)

**Status:** ✅ Backend vollständig funktionsfähig, Authentication funktioniert
**Framework:** Next.js 15 App Router (BEHALTEN!)
**Sprache:** TypeScript
**Styling:** Tailwind CSS + Shadcn/ui

---

## 🏗️ Tech Stack (bereits vorhanden)

```json
{
  "framework": "Next.js 15",
  "router": "App Router",
  "language": "TypeScript",
  "styling": "Tailwind CSS",
  "components": "Shadcn/ui",
  "state": "React Context / Zustand (optional)",
  "charts": "Recharts",
  "forms": "React Hook Form + Zod",
  "api": "Axios",
  "icons": "Lucide React"
}
```

---

## 📊 Verfügbare Backend-Module & Endpoints

### **1. Users Module** (`/api/v1/users`)
- ✅ POST `/login` - User Login
- ✅ POST `/register/benutzer` - Benutzer Registration
- ✅ POST `/register/therapist` - Therapist Registration
- ✅ POST `/logout` - User Logout
- ✅ GET `/profile` - Get User Profile
- ✅ PUT `/profile` - Update User Profile
- ✅ POST `/change-password` - Change Password
- ✅ GET `/platform-statistics` - Platform Statistics

### **2. Mood Module** (`/api/v1/mood`)
- ✅ POST `/` - Create Mood Entry
- ✅ GET `/` - Get Mood Entries (paginated)
- ✅ GET `/{entry_id}` - Get Single Mood Entry
- ✅ PUT `/{entry_id}` - Update Mood Entry
- ✅ DELETE `/{entry_id}` - Delete Mood Entry
- ✅ GET `/analytics/trends` - Get Mood Trends
- ✅ GET `/today/check-in` - Check Today's Mood
- ✅ POST `/quick-entry` - Quick Mood Entry
- ✅ GET `/statistics/personal` - Personal Statistics
- ✅ POST `/encrypted` - Create Encrypted Mood Entry
- ✅ GET `/encrypted` - Get Encrypted Mood Entries
- ✅ GET `/encrypted/{entry_id}` - Get Encrypted Entry
- ✅ DELETE `/encrypted/{entry_id}` - Delete Encrypted Entry

### **3. Dreams Module** (`/api/v1/dreams`)
- ✅ POST `/` - Create Dream Entry
- ✅ GET `/` - Get Dream Entries (paginated)
- ✅ GET `/{entry_id}` - Get Single Dream
- ✅ PUT `/{entry_id}` - Update Dream Entry
- ✅ DELETE `/{entry_id}` - Delete Dream Entry
- ✅ POST `/interpret` - AI Dream Interpretation
- ✅ GET `/statistics` - Dream Statistics
- ✅ GET `/tags` - Get Popular Dream Tags

### **4. Analytics Module** (`/api/v1/analytics`)
- ✅ GET `/overview` - Dashboard Overview Stats
- ✅ GET `/wellness-score` - Wellness Score Calculation
- ✅ GET `/mood/trends` - Mood Trends (7/30/90 days)
- ✅ GET `/mood/patterns` - Mood Patterns & Insights
- ✅ GET `/mood/correlations` - Activity/Mood Correlations
- ✅ GET `/recommendations` - AI Recommendations
- ✅ GET `/insights/weekly` - Weekly Insights Report
- ✅ GET `/insights/monthly` - Monthly Insights Report

### **5. Therapy Module** (`/api/v1/therapy`)
- ✅ POST `/notes` - Create Therapy Note
- ✅ GET `/notes` - Get Therapy Notes (paginated)
- ✅ GET `/notes/{note_id}` - Get Single Note
- ✅ PUT `/notes/{note_id}` - Update Therapy Note
- ✅ DELETE `/notes/{note_id}` - Delete Therapy Note
- ✅ GET `/techniques` - Get Therapy Techniques
- ✅ POST `/sessions` - Create Therapy Session
- ✅ GET `/sessions` - Get Therapy Sessions
- ✅ GET `/progress` - Track Therapy Progress

### **6. Sharing Module** (`/api/v1/sharing`)
- ✅ POST `/share-keys` - Create Share Key
- ✅ GET `/share-keys` - Get Share Keys (as benutzer)
- ✅ GET `/share-keys/therapist` - Get Share Keys (as therapist)
- ✅ POST `/share-keys/{key_id}/accept` - Accept Share Key
- ✅ POST `/share-keys/{key_id}/revoke` - Revoke Share Key
- ✅ GET `/share-keys/{key_id}/access-log` - View Access Log
- ✅ GET `/shared-data/{benutzer_id}` - Get Shared Benutzer Data
- ✅ PUT `/preferences` - Update Sharing Preferences

### **7. Admin Module** (`/api/v1/admin`)
- ✅ GET `/stats` - Admin Dashboard Stats
- ✅ GET `/activity` - Recent System Activity
- ✅ GET `/users` - Get All Users (paginated)
- ✅ PATCH `/users/{user_id}/role` - Update User Role
- ✅ POST `/users/{user_id}/verify` - Verify Therapist
- ✅ POST `/users/{user_id}/reject` - Reject Therapist
- ✅ GET `/pending-therapists` - Get Pending Therapist Verifications

### **8. AI Training Module** (`/api/v1/ai-training`)
- ✅ POST `/datasets` - Create Training Dataset
- ✅ GET `/datasets` - Get Datasets
- ✅ POST `/datasets/{id}/upload` - Upload Dataset File
- ✅ POST `/jobs/start` - Start Training Job
- ✅ GET `/jobs` - Get Training Jobs
- ✅ GET `/jobs/{job_id}` - Get Training Job Details
- ✅ POST `/jobs/{job_id}/stop` - Stop Training Job
- ✅ GET `/models` - Get Model Versions
- ✅ POST `/models/{id}/activate` - Activate Model
- ✅ POST `/models/{id}/deploy` - Deploy Model
- ✅ GET `/predictions/logs` - Get Prediction Logs

---

## 🎯 Feature-Implementierung Roadmap

### **Phase 1: Analytics Dashboard** (Priorität: HOCH)
**Warum zuerst:** Backend komplett ready, hoher Nutzen für User

#### **Komponenten zu bauen:**

1. **Wellness Score Widget** (`components/analytics/WellnessScoreWidget.tsx`)
   - Kreisdiagramm mit Score (0-100)
   - Trend-Indicator (↑↓)
   - Farbcodierung (rot/gelb/grün)
   - Letzte Aktualisierung
   ```tsx
   // API: GET /api/v1/analytics/wellness-score
   {
     score: 75,
     trend: "improving",
     factors: {
       mood: 0.8,
       consistency: 0.7,
       sleep: 0.75
     }
   }
   ```

2. **Mood Trends Chart** (`components/analytics/MoodTrendsChart.tsx`)
   - Line/Bar Chart mit Recharts
   - Zeitraum-Selector (7/30/90 Tage)
   - Mood-Level Visualization
   - Hover-Tooltips mit Details
   ```tsx
   // API: GET /api/v1/analytics/mood/trends?days=30
   {
     trends: [
       { date: "2025-11-01", avgMood: 7.5, entries: 3 },
       ...
     ]
   }
   ```

3. **Mood Patterns Insights** (`components/analytics/MoodPatterns.tsx`)
   - Heatmap für Wochentage
   - Beste/Schlechteste Zeiten
   - Wiederkehrende Muster
   ```tsx
   // API: GET /api/v1/analytics/mood/patterns
   {
     bestDay: "Saturday",
     worstDay: "Monday",
     bestTime: "morning",
     patterns: [...]
   }
   ```

4. **Activity Correlations** (`components/analytics/ActivityCorrelations.tsx`)
   - Aktivitäten vs. Mood Score
   - Positive/Negative Correlations
   - Recommendations basierend auf Daten
   ```tsx
   // API: GET /api/v1/analytics/mood/correlations
   {
     correlations: [
       { activity: "Exercise", impact: +0.8 },
       { activity: "Work", impact: -0.3 }
     ]
   }
   ```

5. **Weekly/Monthly Reports** (`components/analytics/ReportsWidget.tsx`)
   - Zusammenfassung der Woche/Monat
   - Key Insights
   - Progress Tracking
   - Downloadable PDF (optional)
   ```tsx
   // API: GET /api/v1/analytics/insights/weekly
   // API: GET /api/v1/analytics/insights/monthly
   ```

#### **Seiten zu erstellen:**

**`frontend/app/dashboard/analytics/page.tsx`**
```tsx
// Dashboard mit allen Analytics Widgets
// Grid Layout mit Wellness Score, Charts, Insights
// Responsive Design
```

---

### **Phase 2: AI Chat Assistant** (Priorität: HOCH)
**Warum:** Coolster Feature, differenziert die App

#### **Komponenten zu bauen:**

1. **Chat Interface** (`components/chat/ChatInterface.tsx`)
   - WhatsApp/ChatGPT-ähnliches Design
   - Message Bubbles (User vs AI)
   - Auto-scroll to bottom
   - Typing Indicator
   - Timestamp Display

2. **Message Input** (`components/chat/MessageInput.tsx`)
   - Textarea mit Auto-resize
   - Send Button
   - Attachment Button (optional)
   - Character Count
   - Emoji Picker (optional)

3. **Chat Session List** (`components/chat/ChatSessionList.tsx`)
   - Liste aller Chat-Sessions
   - Letzte Nachricht Preview
   - Timestamps
   - New/Unread Badge

4. **AI Response Streaming** (`components/chat/StreamingMessage.tsx`)
   - Typewriter-Effekt für AI Responses
   - Loading Animation
   - Regenerate Button

#### **Features:**
- ✅ Persistent Chat History
- ✅ Multi-Session Support
- ✅ Context-Aware (weiß über Mood Entries Bescheid)
- ✅ Emotional Support Focus
- ✅ Privacy-First (keine externen APIs!)

#### **Seiten:**

**`frontend/app/dashboard/chat/page.tsx`**
```tsx
// Main Chat Interface
// Sidebar mit Sessions
// Active Chat in Main Area
```

**`frontend/app/dashboard/chat/[sessionId]/page.tsx`**
```tsx
// Specific Chat Session
```

---

### **Phase 3: Therapy Notes Interface** (Priorität: MITTEL)
**Warum:** Wichtig für Therapeuten und Benutzeren

#### **Komponenten zu bauen:**

1. **Notes List** (`components/therapy/NotesList.tsx`)
   - Card-basierte Liste
   - Filter nach Datum/Technique
   - Search Funktion
   - Quick Actions (Edit/Delete)

2. **Note Editor** (`components/therapy/NoteEditor.tsx`)
   - Rich Text Editor (Tiptap empfohlen)
   - Formatting Toolbar
   - Save Draft Funktion
   - Auto-save (debounced)

3. **Technique Selector** (`components/therapy/TechniqueSelector.tsx`)
   - Dropdown mit Therapy Techniques
   - Category Grouping (CBT, DBT, Mindfulness, etc.)
   - Description Tooltips

4. **Session Tracker** (`components/therapy/SessionTracker.tsx`)
   - Session Timeline
   - Goals vs Progress
   - Session Notes
   - Next Session Planning

#### **Seiten:**

**`frontend/app/dashboard/therapy/notes/page.tsx`**
```tsx
// Notes List Page
```

**`frontend/app/dashboard/therapy/notes/new/page.tsx`**
```tsx
// Create New Note
```

**`frontend/app/dashboard/therapy/notes/[id]/page.tsx`**
```tsx
// View/Edit Note
```

**`frontend/app/dashboard/therapy/sessions/page.tsx`**
```tsx
// Therapy Sessions Overview
```

---


---

### **Phase 4: Wochenplaner / Kalender** (Priorität: HOCH)
**Warum:** Essentiell für Terminplanung, Therapiesitzungen, Selbstfürsorge-Routinen

#### **Komponenten zu bauen:**

1. **Calendar View** (`components/planner/CalendarView.tsx`)
   - Monatsansicht mit Event-Dots
   - Wochenansicht mit Timeline
   - Tagesansicht mit detailliertem Schedule
   - View-Switcher (Monat/Woche/Tag)
   - Navigation (Prev/Next/Today)
   - Mini-Calendar für schnelle Navigation
   ```tsx
   // Kalendar-Bibliothek: FullCalendar oder react-big-calendar
   // Unterstützt Drag & Drop, Recurring Events, etc.
   ```

2. **Event Creator** (`components/planner/EventCreator.tsx`)
   - Event-Type Selector:
     * 📅 Therapiesitzung
     * 💊 Medikation Reminder
     * 🧘 Selbstfürsorge (Meditation, Sport, etc.)
     * 📝 Journal Reminder
     * 🎯 Persönliche Ziele/Tasks
   - Titel & Beschreibung
   - Datum & Uhrzeit Picker
   - Dauer-Eingabe
   - Recurring Events (täglich, wöchentlich, monatlich)
   - Reminder-Einstellungen (5min, 15min, 1h, 1 Tag vorher)
   - Farb-Auswahl für Kategorien
   - Location/Video-Link (für Online-Sitzungen)

3. **Event Details Modal** (`components/planner/EventDetailsModal.tsx`)
   - Vollständige Event-Informationen
   - Edit/Delete Buttons
   - Mark as Complete
   - Add Notes (nach dem Event)
   - Attach Files/Documents
   - Teilnehmer-Liste (bei Therapiesitzungen)

4. **Recurring Events Manager** (`components/planner/RecurringEventsManager.tsx`)
   - Pattern-Auswahl (täglich, wöchentlich, monatlich)
   - Custom Recurrence Rules
   - End Date oder Occurrence Count
   - Skip Dates/Exceptions
   - Edit Single vs All Occurrences

5. **Reminder System** (`components/planner/ReminderNotifications.tsx`)
   - Browser Push Notifications
   - In-App Notification Bell
   - Email Reminders (optional)
   - Customizable Reminder Times
   - Snooze Funktion

6. **Week Overview Widget** (`components/planner/WeekOverviewWidget.tsx`)
   - Kompakte Wochenübersicht für Dashboard
   - Nächste anstehende Events
   - Today's Schedule
   - Upcoming Therapy Sessions
   - Mood Check-in Reminders

7. **Therapist Schedule Manager** (`components/planner/TherapistSchedule.tsx`)
   - Verfügbarkeitszeiten einstellen
   - Blocker für Urlaub/Abwesenheit
   - Benutzer-Termine einsehen
   - Sitzungs-Historie
   - Warteschlange/Anfragen

8. **Appointment Booking** (`components/planner/AppointmentBooking.tsx`)
   - Benutzer sehen Therapeuten-Verfügbarkeit
   - Termin-Anfrage senden
   - Bestätigung/Ablehnung
   - Reschedule-Funktion
   - Cancellation Policy

#### **Backend-Integration benötigt:**

**Neue API Endpoints (noch zu implementieren):**
```typescript
// Calendar Events
POST   /api/v1/calendar/events          - Create Event
GET    /api/v1/calendar/events          - Get Events (filtered by date range)
GET    /api/v1/calendar/events/{id}     - Get Single Event
PUT    /api/v1/calendar/events/{id}     - Update Event
DELETE /api/v1/calendar/events/{id}     - Delete Event

// Recurring Events
POST   /api/v1/calendar/events/{id}/recurrence  - Set Recurrence
PUT    /api/v1/calendar/events/{id}/recurrence  - Update Recurrence
DELETE /api/v1/calendar/events/{id}/recurrence  - Remove Recurrence

// Therapy Appointments (Therapeuten-Benutzer Interaktion)
POST   /api/v1/therapy/appointments              - Create Appointment
GET    /api/v1/therapy/appointments              - Get Appointments
PUT    /api/v1/therapy/appointments/{id}/status  - Accept/Decline/Reschedule
DELETE /api/v1/therapy/appointments/{id}         - Cancel Appointment

// Availability (für Therapeuten)
POST   /api/v1/therapy/availability     - Set Availability
GET    /api/v1/therapy/availability     - Get Availability
PUT    /api/v1/therapy/availability     - Update Availability

// Reminders
GET    /api/v1/calendar/reminders       - Get Active Reminders
POST   /api/v1/calendar/reminders       - Create Reminder
PUT    /api/v1/calendar/reminders/{id}  - Update Reminder (Snooze, etc.)
DELETE /api/v1/calendar/reminders/{id}  - Dismiss Reminder
```

#### **Database Models benötigt:**

```python
# app/models/calendar.py

class CalendarEvent(Base):
    """Calendar event model"""
    __tablename__ = "calendar_events"
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID, ForeignKey("users.id"), nullable=False)
    
    # Event Details
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    event_type = Column(String(50), nullable=False)  # therapy, medication, selfcare, journal, personal
    
    # Timing
    start_datetime = Column(DateTime, nullable=False)
    end_datetime = Column(DateTime, nullable=False)
    all_day = Column(Boolean, default=False)
    timezone = Column(String(50), default="Europe/Berlin")
    
    # Recurrence
    is_recurring = Column(Boolean, default=False)
    recurrence_rule = Column(JSON, nullable=True)  # RRULE format
    recurrence_exceptions = Column(ARRAY(DateTime), nullable=True)
    parent_event_id = Column(UUID, ForeignKey("calendar_events.id"), nullable=True)
    
    # Reminder
    reminder_enabled = Column(Boolean, default=True)
    reminder_minutes_before = Column(Integer, default=15)
    
    # Metadata
    color = Column(String(20), nullable=True)
    location = Column(String(500), nullable=True)
    video_link = Column(String(500), nullable=True)
    attachments = Column(JSON, nullable=True)
    
    # Status
    status = Column(String(20), default="scheduled")  # scheduled, completed, cancelled
    completed_at = Column(DateTime, nullable=True)
    notes_after = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="calendar_events")
    

class TherapyAppointment(Base):
    """Therapy appointment model (separate from general calendar)"""
    __tablename__ = "therapy_appointments"
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    
    # Participants
    user_id = Column(UUID, ForeignKey("users.id"), nullable=False)
    therapist_id = Column(UUID, ForeignKey("users.id"), nullable=False)
    
    # Appointment Details
    title = Column(String(200), default="Therapy Session")
    description = Column(Text, nullable=True)
    appointment_type = Column(String(50), default="session")  # session, consultation, follow-up
    
    # Timing
    scheduled_start = Column(DateTime, nullable=False)
    scheduled_end = Column(DateTime, nullable=False)
    duration_minutes = Column(Integer, default=50)
    
    # Status
    status = Column(String(20), default="pending")  # pending, confirmed, completed, cancelled, rescheduled
    confirmed_by_therapist_at = Column(DateTime, nullable=True)
    confirmed_by_user_at = Column(DateTime, nullable=True)
    
    # Meeting Details
    location = Column(String(500), nullable=True)
    video_link = Column(String(500), nullable=True)
    meeting_type = Column(String(20), default="video")  # video, in-person, phone
    
    # Rescheduling
    reschedule_reason = Column(Text, nullable=True)
    rescheduled_from_id = Column(UUID, ForeignKey("therapy_appointments.id"), nullable=True)
    
    # Cancellation
    cancelled_at = Column(DateTime, nullable=True)
    cancelled_by_user_id = Column(UUID, ForeignKey("users.id"), nullable=True)
    cancellation_reason = Column(Text, nullable=True)
    
    # Completion
    completed_at = Column(DateTime, nullable=True)
    session_notes_id = Column(UUID, ForeignKey("therapy_notes.id"), nullable=True)
    
    # Reminders
    reminder_sent_at = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="appointments_as_user")
    therapist = relationship("User", foreign_keys=[therapist_id], back_populates="appointments_as_therapist")
    session_notes = relationship("TherapyNote", uselist=False)


class TherapistAvailability(Base):
    """Therapist availability schedule"""
    __tablename__ = "therapist_availability"
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    therapist_id = Column(UUID, ForeignKey("users.id"), nullable=False)
    
    # Day of Week (0 = Monday, 6 = Sunday)
    day_of_week = Column(Integer, nullable=False)
    
    # Time Slots
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    
    # Overrides
    is_available = Column(Boolean, default=True)
    specific_date = Column(Date, nullable=True)  # For specific date overrides (vacation, etc.)
    
    # Metadata
    notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    therapist = relationship("User", back_populates="availability_slots")
```

#### **Seiten:**

**`frontend/app/dashboard/planner/page.tsx`**
```tsx
// Main Planner Page
// Calendar View mit Monat/Woche/Tag Ansichten
// Event Creator
// Upcoming Events Sidebar
```

**`frontend/app/dashboard/planner/events/new/page.tsx`**
```tsx
// Create New Event (Full Page Form)
```

**`frontend/app/dashboard/planner/events/[id]/page.tsx`**
```tsx
// View/Edit Event Details
```

**`frontend/app/therapist/appointments/page.tsx`**
```tsx
// Therapist Appointments Overview
// Pending Requests
// Confirmed Appointments
// Availability Management
```

**`frontend/app/therapist/availability/page.tsx`**
```tsx
// Set Weekly Availability
// Block specific dates
// Manage appointment rules
```

#### **Features:**

✅ **Für alle Benutzer:**
- Persönlicher Kalender
- Event-Erstellung (Selbstfürsorge, Erinnerungen, Ziele)
- Reminder-System
- Recurring Events
- Dashboard Widget mit kommenden Events
- Sync mit Mood/Dreams (z.B. "Daily Mood Check-in" um 20:00 Uhr)

✅ **Für Therapeuten:**
- Verfügbarkeitszeiten einstellen
- Termin-Anfragen annehmen/ablehnen
- Alle Benutzer-Termine einsehen
- Sitzungsnotizen direkt aus Kalender erstellen
- Automatische Reminder an Benutzer

✅ **Für Benutzer (mit Therapeuten):**
- Therapeuten-Verfügbarkeit einsehen
- Termin-Anfragen senden
- Bestätigte Termine im Kalender
- Video-Link für Online-Sitzungen
- Reschedule/Cancel-Optionen

#### **Integration mit anderen Features:**

- 📊 **Analytics:** "Wie oft hattest du Therapiesitzungen?" "Hast du deine Selbstfürsorge-Routinen eingehalten?"
- 📝 **Therapy Notes:** Direkt aus Termin heraus Notizen erstellen
- 🤖 **AI Chat:** "Erinnere mich daran, heute zu meditieren" → Event wird erstellt
- 📈 **Mood Tracking:** Automatische Reminders für Mood Check-ins

#### **Dependencies:**

```bash
# Calendar Component Library (wähle eine)
npm install @fullcalendar/react @fullcalendar/daygrid @fullcalendar/timegrid @fullcalendar/interaction
# ODER
npm install react-big-calendar

# Date Utilities
npm install date-fns  # bereits vorhanden

# RRule für Recurring Events
npm install rrule
```


#### **9. Kalender-Synchronisation (Google Calendar, Outlook, Apple Calendar)**

**Features:**
- 📤 **Export zu externen Kalendern** - iCal/ICS Format
- 📥 **Import von externen Kalendern** - Bestehende Termine importieren
- 🔄 **Zwei-Wege-Synchronisation** - Änderungen werden sync gehalten
- 📧 **Kalender-Abonnement** - Subscribe-URL für externe Apps
- 🔗 **OAuth-Integration** - Sichere Verbindung zu Google/Microsoft

**Implementierung:**

1. **iCal/ICS Export**
```tsx
// components/planner/CalendarExport.tsx
import { Button } from '@/components/ui/button'
import { Download } from 'lucide-react'

export function ExportCalendar() {
  const handleExport = async () => {
    // Get all events from API
    const events = await apiClient.getCalendarEvents()

    // Generate ICS file
    const icsContent = generateICS(events)

    // Download file
    const blob = new Blob([icsContent], { type: 'text/calendar' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'mindbridge-calendar.ics'
    a.click()
  }

  return (
    <Button onClick={handleExport} variant="outline">
      <Download className="mr-2 h-4 w-4" />
      Als ICS exportieren
    </Button>
  )
}

// ICS Generator
function generateICS(events: CalendarEvent[]): string {
  let ics = 'BEGIN:VCALENDAR\\n'
  ics += 'VERSION:2.0\\n'
  ics += 'PRODID:-//MindBridge//Calendar//DE\\n'
  ics += 'CALSCALE:GREGORIAN\\n'

  events.forEach(event => {
    ics += 'BEGIN:VEVENT\\n'
    ics += `UID:${event.id}@mindbridge.app\\n`
    ics += `DTSTAMP:${formatICSDate(event.created_at)}\\n`
    ics += `DTSTART:${formatICSDate(event.start_datetime)}\\n`
    ics += `DTEND:${formatICSDate(event.end_datetime)}\\n`
    ics += `SUMMARY:${event.title}\\n`
    ics += `DESCRIPTION:${event.description || ''}\\n`
    if (event.location) ics += `LOCATION:${event.location}\\n`
    ics += 'END:VEVENT\\n'
  })

  ics += 'END:VCALENDAR'
  return ics
}
```

2. **Kalender-Abonnement (Webcal URL)**
```tsx
// Backend endpoint für Subscribe-URL
GET /api/v1/calendar/subscribe/{user_id}/{token}
// Returns: ICS file mit allen Events
// Auto-updates wenn Calendar gelesen wird

// Frontend Component
export function CalendarSubscription() {
  const [subscribeUrl, setSubscribeUrl] = useState('')

  useEffect(() => {
    // Generate subscribe URL with user token
    const url = `webcal://mindbridge.app/api/v1/calendar/subscribe/${userId}/${token}`
    setSubscribeUrl(url)
  }, [])

  const copyToClipboard = () => {
    navigator.clipboard.writeText(subscribeUrl)
    toast.success('Subscribe-URL kopiert!')
  }

  return (
    <div className="space-y-4">
      <h3>Kalender abonnieren</h3>
      <p className="text-sm text-muted-foreground">
        Füge diese URL in Google Calendar, Apple Calendar oder Outlook ein:
      </p>
      <div className="flex gap-2">
        <Input value={subscribeUrl} readOnly />
        <Button onClick={copyToClipboard}>Kopieren</Button>
      </div>

      <div className="grid grid-cols-3 gap-4 mt-4">
        <Button variant="outline" onClick={() => window.open('https://calendar.google.com/calendar/r/settings/addbyurl')}>
          Google Calendar
        </Button>
        <Button variant="outline">
          Apple Calendar
        </Button>
        <Button variant="outline">
          Outlook
        </Button>
      </div>
    </div>
  )
}
```

3. **Google Calendar Integration (OAuth)**
```tsx
// Integration via Google Calendar API
// components/planner/GoogleCalendarSync.tsx

export function GoogleCalendarSync() {
  const [connected, setConnected] = useState(false)
  const [syncing, setSyncing] = useState(false)

  const connectGoogle = async () => {
    // OAuth Flow
    const authUrl = await apiClient.getGoogleAuthUrl()
    window.location.href = authUrl
  }

  const syncFromGoogle = async () => {
    setSyncing(true)
    try {
      // Import events from Google Calendar
      await apiClient.syncGoogleCalendar('import')
      toast.success('Events von Google Calendar importiert!')
    } catch (error) {
      toast.error('Synchronisation fehlgeschlagen')
    } finally {
      setSyncing(false)
    }
  }

  const syncToGoogle = async () => {
    setSyncing(true)
    try {
      // Export events to Google Calendar
      await apiClient.syncGoogleCalendar('export')
      toast.success('Events zu Google Calendar exportiert!')
    } catch (error) {
      toast.error('Synchronisation fehlgeschlagen')
    } finally {
      setSyncing(false)
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Google Calendar Synchronisation</CardTitle>
      </CardHeader>
      <CardContent>
        {!connected ? (
          <Button onClick={connectGoogle}>
            Mit Google verbinden
          </Button>
        ) : (
          <div className="space-y-4">
            <div className="flex items-center gap-2">
              <CheckCircle className="text-green-500" />
              <span>Verbunden mit Google Calendar</span>
            </div>
            <div className="flex gap-2">
              <Button onClick={syncFromGoogle} disabled={syncing}>
                Von Google importieren
              </Button>
              <Button onClick={syncToGoogle} disabled={syncing}>
                Zu Google exportieren
              </Button>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
```

**Backend Requirements:**

```python
# app/modules/calendar/routes.py

@router.get("/subscribe/{user_id}/{token}")
async def subscribe_calendar(
    user_id: str,
    token: str,
    db: AsyncSession = Depends(get_async_session),
):
    """
    Calendar subscription endpoint (webcal://)
    Returns ICS file for external calendar apps
    """
    # Verify token
    if not verify_subscribe_token(user_id, token):
        raise HTTPException(status_code=401, detail="Invalid token")

    # Get user's events
    events = await get_user_events(db, user_id)

    # Generate ICS
    ics_content = generate_ics_file(events)

    return Response(
        content=ics_content,
        media_type="text/calendar",
        headers={
            "Content-Disposition": "attachment; filename=mindbridge.ics"
        }
    )


@router.post("/sync/google")
async def sync_google_calendar(
    action: str,  # "import" or "export"
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Sync with Google Calendar
    Requires OAuth token stored for user
    """
    # Get user's Google OAuth credentials
    google_creds = await get_google_credentials(db, user_id)

    if action == "import":
        # Import from Google Calendar
        google_events = fetch_google_events(google_creds)
        await import_events(db, user_id, google_events)

    elif action == "export":
        # Export to Google Calendar
        our_events = await get_user_events(db, user_id)
        await push_to_google(google_creds, our_events)

    return {"success": True, "action": action}


@router.get("/oauth/google")
async def google_oauth_callback(
    code: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Google OAuth callback
    Exchanges code for access token and stores it
    """
    # Exchange code for token
    credentials = exchange_code_for_token(code)

    # Store credentials
    await store_google_credentials(db, user_id, credentials)

    return RedirectResponse(url="/dashboard/planner?google_connected=true")
```

**Dependencies:**

```bash
# ICS Generation
npm install ical-generator

# Google Calendar API (backend)
pip install google-auth google-auth-oauthlib google-api-python-client
```

**Unterstützte Kalender-Apps:**
- ✅ Google Calendar (OAuth + Subscribe)
- ✅ Apple Calendar (Subscribe URL)
- ✅ Outlook/Office 365 (Subscribe URL)
- ✅ Thunderbird (ICS Import)
- ✅ Any iCal-compatible app


#### **10. Mobile Kalender-Integration (iOS & Android)**

**Features:**
- 📱 **Native Calendar App Support** - Direkt zu iOS/Android Calendar hinzufügen
- 🔗 **Deep Links** - One-Tap "Add to Calendar" Button
- 📲 **Plattform-Erkennung** - Automatische Anpassung für iOS/Android
- 🔄 **Sync über Subscribe-URL** - Kontinuierliche Synchronisation
- 📥 **ICS Import** - Manuelle Event-Imports

**Implementierung:**

1. **Add to Calendar Button (Universal)**
```tsx
// components/planner/AddToCalendarButton.tsx
import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Calendar, ChevronDown } from 'lucide-react'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'

interface AddToCalendarProps {
  event: {
    title: string
    description: string
    startDate: Date
    endDate: Date
    location?: string
  }
}

export function AddToCalendarButton({ event }: AddToCalendarProps) {
  const [platform, setPlatform] = useState<'ios' | 'android' | 'web'>('web')

  // Detect platform
  useEffect(() => {
    const userAgent = navigator.userAgent.toLowerCase()
    if (/iphone|ipad|ipod/.test(userAgent)) {
      setPlatform('ios')
    } else if (/android/.test(userAgent)) {
      setPlatform('android')
    }
  }, [])

  // Generate ICS file content
  const generateICS = () => {
    const formatDate = (date: Date) => {
      return date.toISOString().replace(/[-:]/g, '').split('.')[0] + 'Z'
    }

    return `BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//MindBridge//Event//DE
BEGIN:VEVENT
UID:${event.id || Date.now()}@mindbridge.app
DTSTAMP:${formatDate(new Date())}
DTSTART:${formatDate(event.startDate)}
DTEND:${formatDate(event.endDate)}
SUMMARY:${event.title}
DESCRIPTION:${event.description || ''}
${event.location ? `LOCATION:${event.location}` : ''}
END:VEVENT
END:VCALENDAR`
  }

  // iOS: Create ICS data URL and trigger download
  const addToiOSCalendar = () => {
    const icsContent = generateICS()
    const blob = new Blob([icsContent], { type: 'text/calendar;charset=utf-8' })
    const url = URL.createObjectURL(blob)

    // Create temporary link and click it
    const link = document.createElement('a')
    link.href = url
    link.download = `${event.title.replace(/\s+/g, '_')}.ics`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
  }

  // Android: Use Google Calendar Intent
  const addToAndroidCalendar = () => {
    const startTime = event.startDate.getTime()
    const endTime = event.endDate.getTime()

    // Google Calendar Intent URL
    const intentUrl = `intent://calendar/0/#Intent;` +
      `scheme=content;` +
      `package=com.android.calendar;` +
      `component=com.android.calendar/com.android.calendar.LaunchActivity;` +
      `S.title=${encodeURIComponent(event.title)};` +
      `S.description=${encodeURIComponent(event.description || '')};` +
      `l.beginTime=${startTime};` +
      `l.endTime=${endTime};` +
      (event.location ? `S.eventLocation=${encodeURIComponent(event.location)};` : '') +
      `end`

    // Fallback to web URL if intent doesn't work
    const webUrl = `https://www.google.com/calendar/render?action=TEMPLATE` +
      `&text=${encodeURIComponent(event.title)}` +
      `&dates=${formatGoogleDate(event.startDate)}/${formatGoogleDate(event.endDate)}` +
      `&details=${encodeURIComponent(event.description || '')}` +
      (event.location ? `&location=${encodeURIComponent(event.location)}` : '')

    // Try intent first, fallback to web
    window.location.href = intentUrl

    // Fallback after 500ms if intent failed
    setTimeout(() => {
      window.open(webUrl, '_blank')
    }, 500)
  }

  // Web: Download ICS file
  const addToWebCalendar = () => {
    addToiOSCalendar() // Same as iOS (ICS download)
  }

  // Format date for Google Calendar URL
  const formatGoogleDate = (date: Date) => {
    return date.toISOString().replace(/[-:]/g, '').split('.')[0] + 'Z'
  }

  const handleAddToCalendar = () => {
    if (platform === 'ios') {
      addToiOSCalendar()
    } else if (platform === 'android') {
      addToAndroidCalendar()
    } else {
      addToWebCalendar()
    }
  }

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="outline" className="gap-2">
          <Calendar className="h-4 w-4" />
          Zum Kalender hinzufügen
          <ChevronDown className="h-4 w-4" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        <DropdownMenuItem onClick={handleAddToCalendar}>
          {platform === 'ios' && '📱 Apple Kalender (iOS)'}
          {platform === 'android' && '📱 Google Kalender (Android)'}
          {platform === 'web' && '💻 ICS-Datei herunterladen'}
        </DropdownMenuItem>
        <DropdownMenuItem onClick={() => window.open(`https://calendar.google.com/calendar/render?action=TEMPLATE&text=${encodeURIComponent(event.title)}&dates=${formatGoogleDate(event.startDate)}/${formatGoogleDate(event.endDate)}&details=${encodeURIComponent(event.description || '')}`, '_blank')}>
          🌐 Google Calendar (Web)
        </DropdownMenuItem>
        <DropdownMenuItem onClick={() => window.open(`https://outlook.office.com/calendar/0/deeplink/compose?subject=${encodeURIComponent(event.title)}&startdt=${event.startDate.toISOString()}&enddt=${event.endDate.toISOString()}&body=${encodeURIComponent(event.description || '')}`, '_blank')}>
          🌐 Outlook Calendar (Web)
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
```

2. **Mobile Subscribe-URL Anleitung**
```tsx
// components/planner/MobileCalendarSync.tsx
import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Copy, Check } from 'lucide-react'

export function MobileCalendarSync() {
  const [subscribeUrl, setSubscribeUrl] = useState('')
  const [copied, setCopied] = useState(false)

  useEffect(() => {
    // Get subscribe URL from API
    const url = `webcal://mindbridge.app/api/v1/calendar/subscribe/${userId}/${token}`
    setSubscribeUrl(url)
  }, [])

  const copyToClipboard = () => {
    navigator.clipboard.writeText(subscribeUrl)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>📱 Mobile Kalender synchronisieren</CardTitle>
      </CardHeader>
      <CardContent>
        <Tabs defaultValue="ios">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="ios">iOS (iPhone/iPad)</TabsTrigger>
            <TabsTrigger value="android">Android</TabsTrigger>
          </TabsList>

          <TabsContent value="ios" className="space-y-4">
            <div className="space-y-2">
              <h4 className="font-medium">Anleitung für iOS:</h4>
              <ol className="list-decimal list-inside space-y-2 text-sm text-muted-foreground">
                <li>Kopiere die Subscribe-URL unten</li>
                <li>Öffne die <strong>Einstellungen</strong> App</li>
                <li>Gehe zu <strong>Kalender</strong> → <strong>Accounts</strong></li>
                <li>Tippe auf <strong>Account hinzufügen</strong></li>
                <li>Wähle <strong>Andere</strong></li>
                <li>Wähle <strong>Kalenderabo hinzufügen</strong></li>
                <li>Füge die kopierte URL ein und tippe auf <strong>Weiter</strong></li>
              </ol>
            </div>

            <div className="flex gap-2">
              <Input value={subscribeUrl} readOnly />
              <Button onClick={copyToClipboard} variant="outline" size="icon">
                {copied ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
              </Button>
            </div>

            <div className="bg-muted p-4 rounded-lg text-sm">
              <strong>💡 Tipp:</strong> Der Kalender wird automatisch synchronisiert.
              Neue Events erscheinen automatisch in deinem iOS Kalender!
            </div>
          </TabsContent>

          <TabsContent value="android" className="space-y-4">
            <div className="space-y-2">
              <h4 className="font-medium">Anleitung für Android:</h4>
              <ol className="list-decimal list-inside space-y-2 text-sm text-muted-foreground">
                <li>Kopiere die Subscribe-URL unten</li>
                <li>Öffne die <strong>Google Kalender</strong> App</li>
                <li>Tippe auf das <strong>Menü</strong> (☰) oben links</li>
                <li>Scrolle nach unten zu <strong>Einstellungen</strong></li>
                <li>Wähle <strong>Kalender hinzufügen</strong></li>
                <li>Wähle <strong>Per URL</strong></li>
                <li>Füge die kopierte URL ein (ändere webcal:// zu https://)</li>
              </ol>
            </div>

            <div className="flex gap-2">
              <Input value={subscribeUrl.replace('webcal://', 'https://')} readOnly />
              <Button
                onClick={() => {
                  navigator.clipboard.writeText(subscribeUrl.replace('webcal://', 'https://'))
                  setCopied(true)
                  setTimeout(() => setCopied(false), 2000)
                }}
                variant="outline"
                size="icon"
              >
                {copied ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
              </Button>
            </div>

            <div className="bg-muted p-4 rounded-lg text-sm">
              <strong>💡 Tipp:</strong> Android verwendet https:// statt webcal://.
              Die URL oben ist bereits angepasst!
            </div>

            <div className="bg-blue-50 dark:bg-blue-950 p-4 rounded-lg text-sm">
              <strong>Alternative:</strong> Verwende die Google Calendar OAuth-Integration
              für Zwei-Wege-Synchronisation (Events von Google → MindBridge und zurück)
            </div>
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  )
}
```

3. **QR-Code für einfache Mobile-Einrichtung**
```tsx
// components/planner/QRCodeSubscribe.tsx
import { useEffect, useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import QRCode from 'qrcode'

export function QRCodeSubscribe() {
  const [qrCodeUrl, setQrCodeUrl] = useState('')

  useEffect(() => {
    const subscribeUrl = `webcal://mindbridge.app/api/v1/calendar/subscribe/${userId}/${token}`

    // Generate QR Code
    QRCode.toDataURL(subscribeUrl, {
      width: 300,
      margin: 2,
      color: {
        dark: '#000000',
        light: '#ffffff',
      },
    }).then(url => {
      setQrCodeUrl(url)
    })
  }, [])

  return (
    <Card>
      <CardHeader>
        <CardTitle>📱 QR-Code scannen</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col items-center gap-4">
        {qrCodeUrl && (
          <img src={qrCodeUrl} alt="Calendar Subscribe QR Code" className="rounded-lg" />
        )}
        <p className="text-sm text-muted-foreground text-center">
          Scanne diesen QR-Code mit deinem Smartphone, um den Kalender zu abonnieren
        </p>
      </CardContent>
    </Card>
  )
}
```

**Dependencies:**

```bash
# QR Code Generation
npm install qrcode
npm install @types/qrcode --save-dev
```

**Platform Detection Helper:**

```typescript
// lib/platform-detection.ts
export function detectPlatform(): 'ios' | 'android' | 'web' {
  if (typeof window === 'undefined') return 'web'

  const userAgent = navigator.userAgent.toLowerCase()

  if (/iphone|ipad|ipod/.test(userAgent)) {
    return 'ios'
  } else if (/android/.test(userAgent)) {
    return 'android'
  }

  return 'web'
}

export function isMobile(): boolean {
  return detectPlatform() !== 'web'
}
```

**Usage in Event Detail Page:**

```tsx
// app/dashboard/planner/events/[id]/page.tsx
import { AddToCalendarButton } from '@/components/planner/AddToCalendarButton'

export default function EventDetailPage({ params }: { params: { id: string } }) {
  const event = useEvent(params.id)

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1>{event.title}</h1>

        {/* One-tap add to calendar */}
        <AddToCalendarButton event={event} />
      </div>

      {/* Rest of event details */}
    </div>
  )
}
```

**Unterstützte Mobile Kalender-Apps:**
- ✅ **iOS:** Apple Kalender (native), Google Calendar App, Outlook App
- ✅ **Android:** Google Calendar (native), Samsung Calendar, Outlook App
- ✅ **Universal:** Webcal Subscribe-URL funktioniert auf beiden Plattformen
- ✅ **Fallback:** ICS-Datei Download für alle anderen Apps

**Mobile-spezifische Features:**
- 📱 Plattform-Erkennung (iOS/Android/Web)
- 🔗 Deep Links zu nativen Calendar Apps
- 📥 ICS-Download für iOS
- 🌐 Google Calendar Intent für Android
- 📲 QR-Code für schnelle Einrichtung
- 🔄 Automatische Synchronisation via Subscribe-URL
- 💾 Offline-Verfügbarkeit (Events werden lokal gespeichert)



### **Phase 5: Data Sharing Hub** (Priorität: MITTEL)
**Warum:** Core Feature für Benutzer-Therapeut Collaboration

#### **Komponenten zu bauen:**

1. **Share Key Generator** (`components/sharing/ShareKeyGenerator.tsx`)
   - Create Share Key Form
   - Permission Checkboxes (Mood/Dreams/Therapy Notes)
   - Expiration Date Picker
   - Copy Share Link Button

2. **Active Shares List** (`components/sharing/ActiveSharesList.tsx`)
   - Liste aller aktiven Share Keys
   - Therapist Info
   - Permissions Preview
   - Revoke Button
   - Access Statistics

3. **Access Log Viewer** (`components/sharing/AccessLogViewer.tsx`)
   - Timeline of Therapist Access
   - What was accessed
   - When accessed
   - Export Log Button

4. **Shared Data Preview** (`components/sharing/SharedDataPreview.tsx`)
   - Preview what Therapist can see
   - Privacy Indicator
   - Data Encryption Status

#### **Seiten:**

**`frontend/app/dashboard/sharing/page.tsx`**
```tsx
// Sharing Overview
// Active Shares
// Create New Share
```

**`frontend/app/therapist/benutzers/[benutzerId]/page.tsx`**
```tsx
// View Shared Benutzer Data (Therapist View)
```

---

### **Phase 6: Settings & Profile** (Priorität: HOCH)
**Warum:** Essential für User Management

#### **Komponenten zu bauen:**

1. **Profile Editor** (`components/settings/ProfileEditor.tsx`)
   - Avatar Upload
   - Name/Email Fields
   - Timezone Selector
   - Language Selector
   - Save Button

2. **Notification Preferences** (`components/settings/NotificationSettings.tsx`)
   - Email Notifications Toggle
   - Push Notifications Toggle
   - Notification Frequency
   - Notification Types (per category)

3. **Privacy Settings** (`components/settings/PrivacySettings.tsx`)
   - Data Sharing Preferences
   - Encryption Settings
   - Data Retention
   - Export Data Button
   - Delete Account Button

4. **Security Settings** (`components/settings/SecuritySettings.tsx`)
   - Change Password Form
   - 2FA Setup (future)
   - Active Sessions
   - Login History

5. **Theme Switcher** (`components/settings/ThemeSwitcher.tsx`)
   - Light/Dark Mode Toggle
   - Color Scheme Selector
   - Font Size Adjuster

#### **Seiten:**

**`frontend/app/dashboard/settings/page.tsx`**
```tsx
// Settings Overview
// Tabs: Profile, Notifications, Privacy, Security
```

---

### **Phase 7: Dashboard Redesign** (Priorität: HOCH)
**Warum:** Zentrale User Experience

#### **Komponenten zu bauen:**

1. **Dashboard Grid** (`components/dashboard/DashboardGrid.tsx`)
   - Responsive Grid Layout
   - Draggable Widgets (optional)
   - Widget Customization

2. **Quick Actions Widget** (`components/dashboard/QuickActions.tsx`)
   - Buttons für häufige Actions
   - "Log Mood", "New Dream", "Chat with AI"
   - Keyboard Shortcuts

3. **Recent Entries Widget** (`components/dashboard/RecentEntries.tsx`)
   - Latest Mood/Dream Entries
   - Quick View
   - Link to Full Entry

4. **Upcoming Sessions** (`components/dashboard/UpcomingSessions.tsx`)
   - Therapy Sessions Calendar
   - Countdown Timer
   - Quick Join Link

5. **Notifications Center** (`components/dashboard/NotificationsCenter.tsx`)
   - Bell Icon mit Badge
   - Dropdown mit Notifications
   - Mark as Read
   - Clear All

6. **Activity Feed** (`components/dashboard/ActivityFeed.tsx`)
   - Timeline of recent activities
   - Achievements/Streaks
   - Milestones

7. **Streak Tracker** (`components/dashboard/StreakTracker.tsx`)
   - Current Streak
   - Best Streak
   - Streak Calendar Heatmap

#### **Seiten:**

**`frontend/app/dashboard/page.tsx`** (REDESIGN)
```tsx
// New Modern Dashboard
// Grid Layout mit allen Widgets
// Welcome Message
// Quick Stats
```

---

## 🎨 Design System

### **Farben (Tailwind)**
```css
/* Light Mode */
--primary: 221 83% 53%        /* Blue */
--secondary: 142 76% 36%      /* Green */
--accent: 45 93% 47%          /* Yellow */
--success: 142 76% 36%        /* Green */
--warning: 45 93% 47%         /* Yellow */
--error: 0 84% 60%            /* Red */
--background: 0 0% 100%       /* White */
--foreground: 222 47% 11%     /* Dark Blue */

/* Dark Mode */
--background: 222 47% 11%     /* Dark Blue */
--foreground: 0 0% 100%       /* White */
```

### **Typography**
```css
font-sans: "Inter", sans-serif
font-mono: "Fira Code", monospace

h1: 2.5rem (40px) - font-bold
h2: 2rem (32px) - font-semibold
h3: 1.5rem (24px) - font-semibold
h4: 1.25rem (20px) - font-medium
body: 1rem (16px) - font-normal
small: 0.875rem (14px) - font-normal
```

### **Spacing**
```css
xs: 0.25rem (4px)
sm: 0.5rem (8px)
md: 1rem (16px)
lg: 1.5rem (24px)
xl: 2rem (32px)
2xl: 3rem (48px)
```

### **Components (Shadcn/ui zu verwenden)**
- ✅ Button
- ✅ Card
- ✅ Input
- ✅ Textarea
- ✅ Select
- ✅ Dialog
- ✅ Dropdown Menu
- ✅ Tabs
- ✅ Toast
- ✅ Alert
- ✅ Badge
- ✅ Avatar
- ✅ Skeleton
- ✅ Progress
- ✅ Slider
- ✅ Switch
- ✅ Checkbox
- ✅ Radio Group
- ✅ Calendar
- ✅ Date Picker

---

## 📁 Dateistruktur (Vorschlag)

```
frontend/
├── app/
│   ├── dashboard/
│   │   ├── page.tsx                    # Main Dashboard (REDESIGN)
│   │   ├── analytics/
│   │   │   └── page.tsx                # Analytics Dashboard (NEU)
│   │   ├── chat/
│   │   │   ├── page.tsx                # Chat Overview (NEU)
│   │   │   └── [sessionId]/
│   │   │       └── page.tsx            # Chat Session (NEU)
│   │   ├── therapy/
│   │   │   ├── notes/
│   │   │   │   ├── page.tsx            # Notes List (NEU)
│   │   │   │   ├── new/
│   │   │   │   │   └── page.tsx        # New Note (NEU)
│   │   │   │   └── [id]/
│   │   │   │       └── page.tsx        # View/Edit Note (NEU)
│   │   │   └── sessions/
│   │   │       └── page.tsx            # Sessions (NEU)
│   │   ├── sharing/
│   │   │   └── page.tsx                # Sharing Hub (NEU)
│   │   ├── settings/
│   │   │   └── page.tsx                # Settings (NEU)
│   │   ├── mood/
│   │   │   ├── page.tsx                # Mood List (VERBESSERN)
│   │   │   ├── new/
│   │   │   │   └── page.tsx            # New Mood
│   │   │   └── [id]/
│   │   │       └── page.tsx            # Mood Details
│   │   └── dreams/
│   │       ├── page.tsx                # Dreams List (VERBESSERN)
│   │       ├── new/
│   │       │   └── page.tsx            # New Dream
│   │       └── [id]/
│   │           └── page.tsx            # Dream Details
│   ├── therapist/
│   │   ├── page.tsx                    # Therapist Dashboard
│   │   ├── benutzers/
│   │   │   ├── page.tsx                # Benutzers List
│   │   │   └── [benutzerId]/
│   │   │       └── page.tsx            # Benutzer Details (VERBESSERN)
│   │   └── share-keys/
│   │       └── page.tsx                # Share Keys Management
│   ├── admin/
│   │   ├── page.tsx                    # Admin Dashboard (VERBESSERN)
│   │   ├── users/
│   │   │   └── page.tsx                # User Management (VERBESSERN)
│   │   ├── models/
│   │   │   └── page.tsx                # AI Models
│   │   ├── training/
│   │   │   └── page.tsx                # Training Jobs
│   │   └── datasets/
│   │       └── page.tsx                # Datasets
│   ├── login/
│   │   └── page.tsx                    # Login
│   └── register/
│       └── page.tsx                    # Register
├── components/
│   ├── analytics/
│   │   ├── WellnessScoreWidget.tsx     # NEU
│   │   ├── MoodTrendsChart.tsx         # NEU
│   │   ├── MoodPatterns.tsx            # NEU
│   │   ├── ActivityCorrelations.tsx    # NEU
│   │   └── ReportsWidget.tsx           # NEU
│   ├── chat/
│   │   ├── ChatInterface.tsx           # NEU
│   │   ├── MessageInput.tsx            # NEU
│   │   ├── ChatSessionList.tsx         # NEU
│   │   └── StreamingMessage.tsx        # NEU
│   ├── therapy/
│   │   ├── NotesList.tsx               # NEU
│   │   ├── NoteEditor.tsx              # NEU
│   │   ├── TechniqueSelector.tsx       # NEU
│   │   └── SessionTracker.tsx          # NEU
│   ├── sharing/
│   │   ├── ShareKeyGenerator.tsx       # NEU
│   │   ├── ActiveSharesList.tsx        # NEU
│   │   ├── AccessLogViewer.tsx         # NEU
│   │   └── SharedDataPreview.tsx       # NEU
│   ├── settings/
│   │   ├── ProfileEditor.tsx           # NEU
│   │   ├── NotificationSettings.tsx    # NEU
│   │   ├── PrivacySettings.tsx         # NEU
│   │   ├── SecuritySettings.tsx        # NEU
│   │   └── ThemeSwitcher.tsx           # NEU
│   ├── dashboard/
│   │   ├── DashboardGrid.tsx           # NEU
│   │   ├── QuickActions.tsx            # NEU
│   │   ├── RecentEntries.tsx           # NEU
│   │   ├── UpcomingSessions.tsx        # NEU
│   │   ├── NotificationsCenter.tsx     # NEU
│   │   ├── ActivityFeed.tsx            # NEU
│   │   └── StreakTracker.tsx           # NEU
│   ├── ui/                             # Shadcn/ui Components
│   │   ├── button.tsx
│   │   ├── card.tsx
│   │   ├── input.tsx
│   │   └── ...
│   └── layout/
│       ├── Sidebar.tsx                 # VERBESSERN
│       ├── Header.tsx                  # VERBESSERN
│       └── Footer.tsx                  # NEU
├── lib/
│   ├── api.ts                          # API Client (bereits vorhanden)
│   ├── utils.ts                        # Utility Functions
│   └── validations.ts                  # Zod Schemas
├── hooks/
│   ├── useAuth.ts                      # Auth Hook
│   ├── useMood.ts                      # Mood Hook
│   ├── useAnalytics.ts                 # Analytics Hook (NEU)
│   ├── useChat.ts                      # Chat Hook (NEU)
│   └── useTheme.ts                     # Theme Hook (NEU)
├── stores/                             # (Optional: Zustand)
│   ├── authStore.ts
│   └── themeStore.ts
└── types/
    ├── index.ts                        # Type Definitions
    └── api.ts                          # API Response Types
```

---

## 🔧 Dependencies hinzufügen

```bash
# Charts
npm install recharts

# Rich Text Editor
npm install @tiptap/react @tiptap/starter-kit

# Form Management
npm install react-hook-form zod @hookform/resolvers

# Date Handling
npm install date-fns

# State Management (optional)
npm install zustand

# Icons (bereits vorhanden)
# lucide-react

# Shadcn/ui Components (nach Bedarf hinzufügen)
npx shadcn-ui@latest add button card input textarea select dialog dropdown-menu tabs toast alert badge avatar skeleton progress slider switch checkbox radio-group calendar
```

---

## 🚀 Implementierungs-Reihenfolge

### **Woche 1: Analytics Dashboard**
1. ✅ WellnessScoreWidget erstellen
2. ✅ MoodTrendsChart mit Recharts
3. ✅ MoodPatterns Component
4. ✅ ActivityCorrelations Component
5. ✅ Analytics Page zusammenbauen
6. ✅ Responsive Design testen

### **Woche 2: AI Chat Assistant**
1. ✅ ChatInterface UI erstellen
2. ✅ MessageInput Component
3. ✅ Chat Session Management
4. ✅ Backend-Integration (Chat API)
5. ✅ Streaming Responses implementieren
6. ✅ Chat History Persistence

### **Woche 3: Therapy Notes**
1. ✅ Rich Text Editor integrieren (Tiptap)
2. ✅ Notes List Component
3. ✅ Note Editor Page
4. ✅ Technique Selector
5. ✅ Session Tracker
6. ✅ Backend-Integration



### **Woche 4: Wochenplaner / Kalender**
1. ✅ Calendar View mit FullCalendar/react-big-calendar
2. ✅ Event Creator Component
3. ✅ Event Details Modal
4. ✅ Recurring Events Manager
5. ✅ Reminder System implementieren
6. ✅ Week Overview Widget
7. ✅ Backend-Endpoints für Calendar erstellen
8. ✅ Therapist Appointments System
### **Woche 5: Data Sharing Hub**
1. ✅ Share Key Generator
2. ✅ Active Shares List
3. ✅ Access Log Viewer
4. ✅ Therapist View für Shared Data
5. ✅ Permission Management
6. ✅ Backend-Integration

### **Woche 6: Settings & Profile**
1. ✅ Profile Editor
2. ✅ Notification Settings
3. ✅ Privacy Settings
4. ✅ Security Settings
5. ✅ Theme Switcher (Dark Mode)
6. ✅ Settings Page Layout

### **Woche 7: Dashboard Redesign**
1. ✅ Dashboard Grid Layout
2. ✅ Quick Actions Widget
3. ✅ Recent Entries Widget
4. ✅ Notifications Center
5. ✅ Activity Feed
6. ✅ Streak Tracker
7. ✅ Final Polish & Testing

---

## 📝 Zusätzliche Features (Nice-to-Have)

### **Advanced Analytics**
- 📊 Export Reports as PDF
- 📧 Email Weekly Reports
- 🎯 Goal Tracking
- 📈 Comparative Analysis (Month vs Month)

### **AI Features**
- 🤖 Voice Input für Chat
- 🎤 Voice Responses
- 📸 Image Analysis (Mood from Photo)
- 🌐 Multi-Language Support

### **Gamification**
- 🏆 Achievement System
- ⭐ Streak Badges
- 📊 Leaderboard (optional, privacy-aware)
- 🎁 Rewards System

### **Mobile App**
- 📱 React Native App
- 🔔 Push Notifications
- 📴 Offline Mode
- 🔄 Background Sync

---

## ✅ Success Criteria

**MVP (Minimum Viable Product):**
- ✅ Analytics Dashboard funktioniert
- ✅ AI Chat funktioniert
- ✅ Mood/Dreams CRUD funktioniert
- ✅ Settings & Profile funktioniert
- ✅ Responsive Design (Desktop + Mobile)
- ✅ Dark Mode Support
- ✅ Authentication funktioniert
- ✅ Alle Backend-Endpoints integriert

**v2.0 Features:**
- ✅ Therapy Notes komplett
- ✅ Data Sharing Hub komplett
- ✅ Gamification Elements
- ✅ Advanced Analytics
- ✅ PDF Export
- ✅ Email Notifications

**Future:**
- ✅ Mobile App (React Native)
- ✅ Voice Features
- ✅ Multi-Language
- ✅ Video Sessions Integration

---

## 🎯 Performance Ziele

- ⚡ **First Load:** < 3 Sekunden
- ⚡ **Route Change:** < 500ms
- ⚡ **API Response:** < 1 Sekunde
- 📦 **Bundle Size:** < 500KB (gzipped)
- 💯 **Lighthouse Score:** > 90

---

## 🔒 Security Checklist

- ✅ httpOnly Cookies für Auth
- ✅ CSRF Protection
- ✅ XSS Prevention
- ✅ Input Validation (Zod)
- ✅ Rate Limiting
- ✅ Encrypted Data Storage
- ✅ Secure Headers
- ✅ No sensitive data in localStorage

---

## 📚 Dokumentation

**Für Entwickler:**
- ✅ Component Documentation (JSDoc)
- ✅ API Integration Guide
- ✅ Style Guide
- ✅ Git Workflow

**Für User:**
- ✅ User Guide (in-app)
- ✅ Tutorial Videos
- ✅ FAQ Section
- ✅ Help Center

---

## 🎬 Getting Started (Nächste Sitzung)

**Schritt 1:** Dependencies installieren
```bash
cd frontend
npm install recharts @tiptap/react @tiptap/starter-kit react-hook-form zod @hookform/resolvers date-fns
```

**Schritt 2:** Shadcn/ui Components hinzufügen
```bash
npx shadcn-ui@latest add button card input textarea select dialog tabs toast alert badge avatar skeleton progress
```

**Schritt 3:** Analytics Dashboard starten
```bash
# Erstelle neue Seite
mkdir -p app/dashboard/analytics
touch app/dashboard/analytics/page.tsx

# Erstelle Components
mkdir -p components/analytics
touch components/analytics/WellnessScoreWidget.tsx
touch components/analytics/MoodTrendsChart.tsx
```

**Schritt 4:** Erste Component bauen
```tsx
// components/analytics/WellnessScoreWidget.tsx
// Siehe Implementierungsdetails unten
```

---

## 💡 Hilfreiche Ressourcen

- **Recharts Docs:** https://recharts.org/
- **Tiptap Docs:** https://tiptap.dev/
- **Shadcn/ui:** https://ui.shadcn.com/
- **React Hook Form:** https://react-hook-form.com/
- **Zod:** https://zod.dev/
- **Next.js 15 Docs:** https://nextjs.org/docs

---

## ✨ Zusammenfassung

**Was haben wir:**
- ✅ Funktionierendes Backend mit 8 Modulen
- ✅ Authentication komplett
- ✅ Basis-Frontend mit Next.js 15

**Was bauen wir:**
- 🎨 Komplettes Frontend-Redesign
- 📊 Analytics Dashboard
- 🤖 AI Chat Assistant
- 📝 Therapy Notes Interface
- 🤝 Data Sharing Hub
- 📅 Wochenplaner / Kalender
- ⚚️ Settings & Profile Pages
- 🏠 Modern Dashboard
- 🌙 Dark Mode (Hell/Dunkel/System)

**Zeitplan:**
- 📅 7 Wochen für komplettes Makeover
- 🎯 1 Woche pro Hauptfeature
- 🌙 Dark Mode parallel implementiert
- ✅ Agile Entwicklung, iterativ

**Nächster Schritt:**
START WITH ANALYTICS DASHBOARD! 📊

---

**Viel Erfolg! 🚀**

---

## 🌙 Dark Mode Implementation

### **Warum Dark Mode?**
- 👁️ Reduziert Augenbelastung bei Nachtnutzung
- 🔋 Spart Batterie auf OLED-Displays
- 😎 Moderner Look & Feel
- 🎨 Bessere Accessibility für lichtempfindliche Benutzer

### **Implementierungs-Ansatz:**

#### **1. Next.js + Tailwind Dark Mode**

```typescript
// tailwind.config.ts
export default {
  darkMode: 'class', // oder 'media' für System-Preference
  theme: {
    extend: {
      colors: {
        // Light Mode
        background: 'hsl(var(--background))',
        foreground: 'hsl(var(--foreground))',
        // Dark Mode - automatisch via Tailwind
      }
    }
  }
}
```

```css
/* app/globals.css */
@layer base {
  :root {
    --background: 0 0% 100%;           /* White */
    --foreground: 222 47% 11%;         /* Dark Blue */
    --primary: 221 83% 53%;            /* Blue */
    --secondary: 142 76% 36%;          /* Green */
    --accent: 45 93% 47%;              /* Yellow */
    --card: 0 0% 100%;                 /* White */
    --card-foreground: 222 47% 11%;    /* Dark Blue */
    --muted: 210 40% 96%;              /* Light Gray */
    --muted-foreground: 215 16% 47%;   /* Mid Gray */
    --border: 214 32% 91%;             /* Light Border */
  }

  .dark {
    --background: 222 47% 11%;         /* Dark Blue */
    --foreground: 210 40% 98%;         /* Light */
    --primary: 217 91% 60%;            /* Lighter Blue */
    --secondary: 142 76% 36%;          /* Green (same) */
    --accent: 45 93% 47%;              /* Yellow (same) */
    --card: 222 47% 15%;               /* Dark Card */
    --card-foreground: 210 40% 98%;    /* Light Text */
    --muted: 217 33% 17%;              /* Dark Muted */
    --muted-foreground: 215 20% 65%;   /* Mid Gray */
    --border: 217 33% 20%;             /* Dark Border */
  }
}
```

#### **2. Theme Provider Component**

```tsx
// components/providers/ThemeProvider.tsx
'use client'

import { createContext, useContext, useEffect, useState } from 'react'

type Theme = 'light' | 'dark' | 'system'

type ThemeContextType = {
  theme: Theme
  setTheme: (theme: Theme) => void
  actualTheme: 'light' | 'dark'
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined)

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [theme, setTheme] = useState<Theme>('system')
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
    const stored = localStorage.getItem('theme') as Theme
    if (stored) {
      setTheme(stored)
    }
  }, [])

  useEffect(() => {
    if (!mounted) return

    const root = document.documentElement
    root.classList.remove('light', 'dark')

    if (theme === 'system') {
      const systemTheme = window.matchMedia('(prefers-color-scheme: dark)').matches
        ? 'dark'
        : 'light'
      root.classList.add(systemTheme)
    } else {
      root.classList.add(theme)
    }

    localStorage.setItem('theme', theme)
  }, [theme, mounted])

  const actualTheme: 'light' | 'dark' = 
    theme === 'system'
      ? (typeof window !== 'undefined' && 
         window.matchMedia('(prefers-color-scheme: dark)').matches 
         ? 'dark' 
         : 'light')
      : theme

  return (
    <ThemeContext.Provider value={{ theme, setTheme, actualTheme }}>
      {children}
    </ThemeContext.Provider>
  )
}

export const useTheme = () => {
  const context = useContext(ThemeContext)
  if (!context) throw new Error('useTheme must be used within ThemeProvider')
  return context
}
```

#### **3. Theme Switcher Component**

```tsx
// components/settings/ThemeSwitcher.tsx
'use client'

import { Moon, Sun, Monitor } from 'lucide-react'
import { useTheme } from '@/components/providers/ThemeProvider'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'

export function ThemeSwitcher() {
  const { theme, setTheme, actualTheme } = useTheme()

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="outline" size="icon">
          {actualTheme === 'dark' ? (
            <Moon className="h-5 w-5" />
          ) : (
            <Sun className="h-5 w-5" />
          )}
          <span className="sr-only">Toggle theme</span>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        <DropdownMenuItem onClick={() => setTheme('light')}>
          <Sun className="mr-2 h-4 w-4" />
          Hell
        </DropdownMenuItem>
        <DropdownMenuItem onClick={() => setTheme('dark')}>
          <Moon className="mr-2 h-4 w-4" />
          Dunkel
        </DropdownMenuItem>
        <DropdownMenuItem onClick={() => setTheme('system')}>
          <Monitor className="mr-2 h-4 w-4" />
          System
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
```

#### **4. Integration in Layout**

```tsx
// app/layout.tsx
import { ThemeProvider } from '@/components/providers/ThemeProvider'

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="de" suppressHydrationWarning>
      <body className="bg-background text-foreground">
        <ThemeProvider>
          {children}
        </ThemeProvider>
      </body>
    </html>
  )
}
```

#### **5. Dark Mode für Components**

```tsx
// Beispiel: Card Component
<Card className="bg-card text-card-foreground border-border">
  <CardHeader>
    <CardTitle>Wellness Score</CardTitle>
  </CardHeader>
  <CardContent>
    {/* Content hier */}
  </CardContent>
</Card>

// Beispiel: Custom Dark Mode Styles
<div className="bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100">
  {/* Content mit expliziten Dark Mode Styles */}
</div>

// Beispiel: Charts (Recharts)
<ResponsiveContainer width="100%" height={300}>
  <LineChart data={data}>
    <Line 
      stroke="hsl(var(--primary))"  // Automatisch hell/dunkel
      strokeWidth={2}
    />
    <CartesianGrid 
      stroke="hsl(var(--border))"   // Automatisch hell/dunkel
      strokeDasharray="3 3"
    />
  </LineChart>
</ResponsiveContainer>
```

#### **6. Theme Toggle im Header**

```tsx
// components/layout/Header.tsx
import { ThemeSwitcher } from '@/components/settings/ThemeSwitcher'

export function Header() {
  return (
    <header className="border-b border-border bg-background">
      <div className="container flex items-center justify-between py-4">
        <Logo />
        <nav>{/* Navigation */}</nav>
        <div className="flex items-center gap-4">
          <NotificationBell />
          <ThemeSwitcher />  {/* ← Theme Toggle Button */}
          <UserMenu />
        </div>
      </div>
    </header>
  )
}
```

#### **7. System Preference Detection**

```tsx
// Automatisch System-Theme übernehmen
useEffect(() => {
  const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
  
  const handleChange = (e: MediaQueryListEvent) => {
    if (theme === 'system') {
      // Update UI when system preference changes
      const root = document.documentElement
      root.classList.remove('light', 'dark')
      root.classList.add(e.matches ? 'dark' : 'light')
    }
  }
  
  mediaQuery.addEventListener('change', handleChange)
  return () => mediaQuery.removeEventListener('change', handleChange)
}, [theme])
```

#### **8. Smooth Transition**

```css
/* app/globals.css */
* {
  transition: background-color 0.3s ease, color 0.3s ease, border-color 0.3s ease;
}
```

### **Dark Mode Checklist:**

✅ **Components:**
- [ ] Button - dark:bg-primary-dark
- [ ] Card - dark:bg-card
- [ ] Input - dark:bg-input dark:text-foreground
- [ ] Select - dark:bg-input
- [ ] Dialog/Modal - dark:bg-card
- [ ] Table - dark:border-border
- [ ] Charts - Use CSS variables for colors
- [ ] Icons - Automatic color inversion
- [ ] Images - Consider filter: brightness() for dark mode

✅ **Pages:**
- [ ] Dashboard - Dark backgrounds
- [ ] Analytics - Chart colors work in dark mode
- [ ] Chat - Message bubbles readable
- [ ] Settings - All form elements styled
- [ ] Planner - Calendar readable in dark mode

✅ **Testing:**
- [ ] Test all components in Light Mode
- [ ] Test all components in Dark Mode
- [ ] Test System Theme detection
- [ ] Test Theme persistence (localStorage)
- [ ] Test smooth transitions
- [ ] Test on mobile devices
- [ ] Test OLED black option (optional)

### **Advanced: OLED Black Mode**

```tsx
// Optional: True black for OLED displays
const themes = {
  light: { /* ... */ },
  dark: { 
    background: '222 47% 11%',  // Dark gray
    /* ... */
  },
  oled: {
    background: '0 0% 0%',      // True black
    card: '0 0% 5%',            // Almost black
    /* ... */
  }
}
```

### **Dependencies:**

```bash
# Keine zusätzlichen Dependencies!
# Tailwind CSS + Next.js haben alles eingebaut
```

---
