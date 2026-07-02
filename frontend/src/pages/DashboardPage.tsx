import { VoicePanel } from '@/features/voice/VoicePanel'
import { EmailPanel } from '@/features/email/EmailPanel'
import { CalendarPanel } from '@/features/calendar/CalendarPanel'

export const DashboardPage = () => (
  <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
    {/* Left column: Email (takes 2/3) */}
    <div className="xl:col-span-2 flex flex-col gap-6">
      <section>
        <h2 className="text-sm font-semibold text-slate-500 uppercase tracking-wide mb-3">Email</h2>
        <EmailPanel />
      </section>
    </div>

    {/* Right column: Voice + Calendar stacked (takes 1/3) */}
    <div className="xl:col-span-1 flex flex-col gap-6">
      <section>
        <h2 className="text-sm font-semibold text-slate-500 uppercase tracking-wide mb-3">Voice Assistant</h2>
        <VoicePanel />
      </section>
      <section>
        <h2 className="text-sm font-semibold text-slate-500 uppercase tracking-wide mb-3">Calendar</h2>
        <CalendarPanel />
      </section>
    </div>
  </div>
)
