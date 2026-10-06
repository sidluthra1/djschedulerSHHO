# Seeds the site with realistic demo activity: fictional teachers and students, upcoming and past
# lessons, signups/waitlists, class requests, role requests and message threads. Dates are relative to
# the day the command runs, so re-running it later refreshes the calendar. Safe to re-run: everything it
# created last time is removed first.

import random
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from django.contrib.auth.models import User
from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from lessonscheduler.models import ClassRequest, ClassSignup, Lesson
from messaging.models import Message, MessageAttachment
from users.models import Profile, RoleChangeRequest

ET = ZoneInfo("America/New_York")
DEMO_EMAIL_DOMAIN = "demo.shho.example"
DEMO_PASSWORD = "shho-demo-2026"

# (username, first, last, role)
DEMO_TEACHERS = [
    ("demo_teacher", "Jordan", "Hayes", "teacher"),
    ("dj_marcus", "Marcus", "Bell", "teacher"),
    ("dj_priya", "Priya", "Raman", "teacher"),
    ("dj_tyrell", "Tyrell", "Washington", "teacher"),
    ("prod_nina", "Nina", "Okafor", "producer"),
    ("prod_leo", "Leo", "Fischer", "producer"),
]
DEMO_STUDENTS = [
    ("demo_student", "Alex", "Rivera"),
    ("maya_c", "Maya", "Chen"),
    ("dre_j", "Andre", "Johnson"),
    ("sofia_m", "Sofia", "Martinez"),
    ("kwame_a", "Kwame", "Asante"),
    ("hannah_b", "Hannah", "Brooks"),
    ("ethan_p", "Ethan", "Park"),
    ("zara_k", "Zara", "Khan"),
    ("liam_o", "Liam", "O'Connor"),
    ("imani_w", "Imani", "Wright"),
    ("noah_g", "Noah", "Garcia"),
    ("ava_t", "Ava", "Thompson"),
    ("jalen_r", "Jalen", "Reed"),
    ("chloe_d", "Chloe", "Dubois"),
    ("marco_s", "Marco", "Silva"),
    ("tess_l", "Tess", "Lindqvist"),
]
DEMO_BIOS = {
    "demo_teacher": "Resident DJ at SHHO events for three years. I teach beatmatching, phrasing and reading a crowd.",
    "dj_marcus": "Turntablist. Scratch battles, routines and anything on vinyl.",
    "dj_priya": "Open-format DJ: hip-hop, Afrobeats and Bollywood blends. Serato and rekordbox.",
    "dj_tyrell": "Club and party DJ. I'll teach you how to keep a dance floor going all night.",
    "prod_nina": "Producer and engineer. FL Studio, sampling and mixdowns that actually translate.",
    "prod_leo": "Ableton Live and hardware. Drum programming, sound design and the SP-404.",
    "demo_student": "Second-year, learning to DJ so I can play the next SHHO showcase.",
}

# Pre-existing test lessons from development that shouldn't be shown off: (title, dj username).
JUNK_LESSONS = [
    ("First Class", "ayaan"), ("ML Class", "ml_at_uva"), ("Second Class", "ayaan"),
    ("DJ class", "elsa"), ("Take 2", "elsa"), ("one class", "ayaan"), ("DJ Class", "rachel"),
    ("ayaan's class", "ayaan"), ("ayaan 2", "ayaan"), ("Sid", "jaylen"), ("fghjk", "siddarth"),
    ("producer class", "ayaan"),
]

LOCATIONS = [
    "Newcomb Hall, Room 481", "Clemons Library, Robertson Media Center", "Old Cabell Hall B012",
    "Student Activities Building, Studio 2", "Ruffner Hall 128", "Rice Hall 130",
    "Brooks Hall Commons", "Newcomb Hall Ballroom",
]

# (title, skill, minutes, capacity, description, teacher username)
# Teachers prefixed with "@" are existing accounts that only post lessons; everything else is fictional.
UPCOMING = [
    ("Beatmatching Fundamentals", "Beginner", 90, 8, "Learn to match tempos by ear and with the pitch fader. Controllers provided, bring headphones.", "demo_teacher"),
    ("Scratching 101: Baby Scratch to Chirps", "Beginner", 60, 6, "Hands-on intro to scratching on real turntables. We'll cover the baby, forward, tear and chirp.", "dj_marcus"),
    ("FL Studio Basics: Your First Beat", "Beginner", 120, 10, "From an empty project to a finished 8-bar loop. Laptops with FL Studio available, or bring your own.", "prod_nina"),
    ("Phrasing & Transitions", "Intermediate", 90, 8, "Stop train-wrecking your mixes. Counting bars, mixing on the phrase and five go-to transitions.", "demo_teacher"),
    ("Open Format Blends", "Intermediate", 90, 6, "Moving between hip-hop, Afrobeats and amapiano without clearing the floor.", "dj_priya"),
    ("Drum Programming in Ableton", "Intermediate", 90, 8, "Swing, ghost notes and layering. Make drums that knock.", "prod_leo"),
    ("Halloween Party Set Prep", "Intermediate", 120, 10, "Build and rehearse a 30-minute set for the SHHO Halloween party. Best set gets a slot at the event.", "dj_tyrell"),
    ("DJing for Absolute Beginners", "Beginner", 90, 10, "No experience needed. Controller basics, EQ and your first mix.", "@sajid"),
    ("Sampling Soul Records", "Proficient", 120, 6, "Chopping, flipping and clearing samples. We'll dig through crates from the SHHO vinyl collection.", "prod_nina"),
    ("Reading a Crowd", "Proficient", 60, 12, "Song selection, energy curves and when to break the rules. Lots of examples from real sets.", "demo_teacher"),
    ("Hip-Hop 101: Golden Era Listening Session", "Beginner", 90, 15, "Listening session and discussion on 1988-1996 hip-hop and the DJs behind it.", "@jaylen"),
    ("Scratch Routines & Combos", "Advanced", 90, 4, "Flares, crabs and building a 1-minute routine. Must be comfortable with basic scratches.", "dj_marcus"),
    ("SP-404 Live Looping", "Intermediate", 90, 5, "Performing beats live on the SP-404: resampling, effects and pad layout.", "prod_leo"),
    ("Club Night Practice Session", "Intermediate", 120, 8, "Open practice on the club setup (CDJs + mixer). Sign up for a 15-minute slot and get feedback.", "dj_tyrell"),
    ("Mixing & Mastering Basics", "Intermediate", 120, 8, "EQ, compression and loudness. Bring a beat you've made and we'll mix it down together.", "prod_nina"),
    ("Open Decks Night", "Beginner", 150, 12, "Casual open decks. Everyone gets a turn, all levels welcome.", "@simone"),
    ("Advanced Blends & EQ Tricks", "Advanced", 90, 6, "Acapella blends, filter sweeps and three-deck mixing.", "dj_priya"),
    ("House Music Foundations", "Beginner", 90, 10, "Four-on-the-floor mixing, long blends and the history of house.", "@keegan"),
    ("Building a Showcase Set", "Proficient", 120, 6, "Plan, practice and record a 20-minute set for the end-of-semester SHHO showcase.", "demo_teacher"),
    ("808s & Bass Design", "Intermediate", 90, 8, "Tuning 808s, saturation and making bass sit right on small speakers.", "prod_leo"),
]
# (title, skill, minutes, capacity, description, teacher) for lessons that already happened this semester.
PAST = [
    ("Welcome Back Open Decks", "Beginner", 150, 15, "Kickoff open decks for the semester.", "dj_tyrell"),
    ("Controller Setup & Basics", "Beginner", 90, 10, "Getting comfortable on the DDJ controllers.", "demo_teacher"),
    ("Intro to Scratching", "Beginner", 60, 6, "First steps on the turntables.", "dj_marcus"),
    ("Beat Making Workshop", "Beginner", 120, 10, "Make a beat in two hours.", "prod_nina"),
    ("EQ & Gain Staging", "Intermediate", 90, 8, "Clean mixes start with levels.", "demo_teacher"),
    ("Afrobeats Mixing", "Intermediate", 90, 8, "Mixing Afrobeats and amapiano.", "dj_priya"),
    ("Ableton Session View Jam", "Intermediate", 90, 6, "Performing with Session View.", "prod_leo"),
    ("Hip-Hop Production History", "Beginner", 90, 15, "From the SP-1200 to today.", "@jaylen"),
]

CONVERSATIONS = [
    ("demo_student", "demo_teacher", [
        "Hey! I signed up for Beatmatching Fundamentals. Do I need to bring my own headphones?",
        "Hey Alex! Yes if you have them, otherwise we have a couple of spare pairs.",
        "Cool, I have some. Also is it ok if I've never touched a controller before?",
        "Totally, that's what the class is for. We start from zero.",
        "Awesome, see you there!",
    ]),
    ("maya_c", "demo_teacher", [
        "Hi Jordan, I'm on the waitlist for Phrasing & Transitions. Any chance a spot opens up?",
        "People usually drop a day or two before. You'll get an automatic message if you're moved in.",
        "Thanks!",
    ]),
    ("demo_student", "dj_marcus", [
        "Hi Marcus, are the scratch classes on real turntables or controllers?",
        "Real turntables! Technics 1200s and a Rane mixer.",
        "No way, that's sick. I'm on the waitlist for Scratching 101.",
        "I'll probably run another section in a few weeks if the waitlist stays long.",
    ]),
    ("dre_j", "prod_nina", [
        "Loved the beat making workshop. Is there a good free alternative to FL Studio for practicing at home?",
        "FL has a free trial that saves projects, you just can't reopen them. GarageBand works too if you're on a Mac.",
        "Got it, thanks Nina.",
    ]),
    ("demo_teacher", "dj_tyrell", [
        "Are we co-hosting the Halloween party practice or are you running it solo?",
        "Solo is fine, but come through if you're free. Could use a second set of ears.",
        "Bet, I'll stop by after my 6pm class.",
    ]),
    ("sofia_m", "demo_student", [
        "Are you going to the Open Decks night?",
        "Yeah! Signed up already. You?",
        "Yep, let's go together. Meet at Newcomb at 7?",
        "Works for me",
    ]),
    ("kwame_a", "prod_leo", [
        "Is the SP-404 class good if I've only used Ableton?",
        "Definitely. A lot of the workflow is the same, just with pads instead of a mouse.",
    ]),
    ("hannah_b", "dj_priya", [
        "Your Afrobeats class was so fun. Can you share the tracklist?",
        "Of course! Sending it over in a bit.",
        "Thank you!!",
    ]),
    ("demo_student", "prod_nina", [
        "Hi Nina, I sent a request for a one-on-one mixing session. Let me know if the time doesn't work.",
    ]),
]


class Command(BaseCommand):
    help = "Populate the database with realistic demo activity (safe to re-run)."

    def handle(self, *args, **options):
        self.rng = random.Random(3240)
        self.now = timezone.now()
        self.today = timezone.localtime(self.now, ET).date()
        with transaction.atomic():
            self.clear_previous_seed()
            self.delete_junk_lessons()
            self.clear_missing_files()
            self.create_users()
            self.create_lessons()
            self.create_signups()
            self.create_class_requests()
            self.create_role_requests()
            self.create_messages()
        self.stdout.write(self.style.SUCCESS(
            f"Seeded {Lesson.objects.count()} lessons ({Lesson.objects.filter(start_time__gte=self.now).count()} upcoming), "
            f"{ClassSignup.objects.count()} signups, {ClassRequest.objects.count()} class requests, "
            f"{Message.objects.count()} messages, {User.objects.count()} users."
        ))

    # --- helpers -------------------------------------------------------------------------------

    def at(self, days, hour, minute=0):
        """Aware datetime `days` from today at a wall-clock time in Charlottesville."""
        return datetime.combine(self.today + timedelta(days=days), time(hour, minute), tzinfo=ET)

    def user(self, username):
        return User.objects.get(username=username.lstrip("@"))

    # --- cleanup -------------------------------------------------------------------------------

    def clear_previous_seed(self):
        # Lessons a previous run posted under existing accounts, matched on (title, teacher) so real
        # lessons that happen to share a title are left alone. Everything else cascades from the users.
        for title, *_, dj in UPCOMING + PAST:
            if dj.startswith("@"):
                Lesson.objects.filter(title=title, dj__username=dj[1:]).delete()
        User.objects.filter(email__endswith=f"@{DEMO_EMAIL_DOMAIN}").delete()

    def delete_junk_lessons(self):
        for title, dj in JUNK_LESSONS:
            Lesson.objects.filter(title=title, dj__username=dj).delete()

    def clear_missing_files(self):
        """Uploads from the old site lived in an S3 bucket that no longer exists; drop dangling references."""
        for profile in Profile.objects.exclude(profile_picture="", intro_audio=""):
            changed = False
            for field in ("profile_picture", "intro_audio"):
                f = getattr(profile, field)
                if f and not default_storage.exists(f.name):
                    setattr(profile, field, None)
                    changed = True
            if changed:
                profile.save(update_fields=["profile_picture", "intro_audio"])
        for lesson in Lesson.objects.exclude(image=""):
            if lesson.image and not default_storage.exists(lesson.image.name):
                Lesson.objects.filter(pk=lesson.pk).update(image=None)
        for attachment in MessageAttachment.objects.all():
            if not default_storage.exists(attachment.image.name):
                attachment.delete()

    # --- creation ------------------------------------------------------------------------------

    def make_user(self, username, first, last, role, days_ago):
        u = User.objects.create(
            username=username, first_name=first, last_name=last,
            email=f"{username}@{DEMO_EMAIL_DOMAIN}",
        )
        if username.startswith("demo_"):
            u.set_password(DEMO_PASSWORD)
        else:
            u.set_unusable_password()
        u.date_joined = self.now - timedelta(days=days_ago, hours=self.rng.randint(0, 23))
        u.last_login = self.now - timedelta(days=self.rng.randint(0, 6), hours=self.rng.randint(0, 23))
        u.save()
        Profile.objects.filter(user=u).update(role=role, bio=DEMO_BIOS.get(username, ""))
        return u

    def create_users(self):
        self.teachers = {u: self.make_user(u, f, l, r, self.rng.randint(40, 70)) for u, f, l, r in DEMO_TEACHERS}
        self.students = {u: self.make_user(u, f, l, "student", self.rng.randint(5, 45)) for u, f, l in DEMO_STUDENTS}

    def create_lessons(self):
        self.upcoming, self.past = [], []
        start_hours = [17, 18, 18, 19, 19, 20]
        day = 1
        for i, (title, skill, minutes, cap, desc, dj) in enumerate(UPCOMING):
            day += self.rng.choice([1, 1, 2, 2, 3])
            start = self.at(day, self.rng.choice(start_hours), self.rng.choice([0, 0, 30]))
            lesson = Lesson(
                title=title, description=desc, location=LOCATIONS[i % len(LOCATIONS)], capacity=cap,
                experience_requirements=skill, start_time=start, end_time=start + timedelta(minutes=minutes),
                dj=self.user(dj), created_at=self.now - timedelta(days=self.rng.randint(2, 14)),
            )
            lesson.save()
            self.upcoming.append(lesson)

        # Past lessons can't go through Lesson.save() (it requires a future start), so insert directly.
        day = 0
        past = []
        for i, (title, skill, minutes, cap, desc, dj) in enumerate(PAST):
            day -= self.rng.choice([3, 4, 5])
            start = self.at(day, self.rng.choice(start_hours))
            past.append(Lesson(
                title=title, description=desc, location=LOCATIONS[(i + 3) % len(LOCATIONS)], capacity=cap,
                experience_requirements=skill, start_time=start, end_time=start + timedelta(minutes=minutes),
                dj=self.user(dj), created_at=start - timedelta(days=self.rng.randint(5, 12)),
            ))
        self.past = Lesson.objects.bulk_create(past)

    def create_signups(self):
        student_pool = [s for name, s in self.students.items() if name != "demo_student"]
        demo = self.students["demo_student"]
        demo_confirmed = {"Beatmatching Fundamentals", "Open Decks Night", "FL Studio Basics: Your First Beat",
                          "Halloween Party Set Prep", "Hip-Hop 101: Golden Era Listening Session"}
        demo_waitlisted = {"Scratching 101: Baby Scratch to Chirps"}

        for lesson in self.upcoming:
            # Popular beginner classes fill up and get waitlists; advanced ones stay partly open.
            fill = {"Beginner": 1.0, "Intermediate": 0.8, "Proficient": 0.6, "Advanced": 0.7}[lesson.experience_requirements]
            confirmed = min(lesson.capacity, max(1, round(lesson.capacity * fill * self.rng.uniform(0.6, 1.1))))
            if lesson.title in demo_waitlisted:
                confirmed = lesson.capacity
            chosen = self.rng.sample(student_pool, min(len(student_pool), confirmed + 3))
            if lesson.title in demo_confirmed:
                chosen = [demo] + [s for s in chosen if s != demo][: confirmed - 1] + chosen[confirmed - 1:]
            waitlist_size = self.rng.randint(1, 3) if confirmed >= lesson.capacity else 0
            for idx, student in enumerate(chosen[: confirmed + waitlist_size]):
                ClassSignup(
                    student=student, lesson=lesson,
                    status="confirmed" if idx < confirmed else "waitlisted",
                    signed_up_at=lesson.created_at + timedelta(hours=6 + idx * self.rng.randint(3, 20)),
                ).save()
            if lesson.title in demo_waitlisted:
                ClassSignup(student=demo, lesson=lesson, status="waitlisted",
                            signed_up_at=self.now - timedelta(days=1)).save()

        past_signups = []
        for lesson in self.past:
            attendees = self.rng.sample(student_pool, min(len(student_pool), self.rng.randint(lesson.capacity // 2, lesson.capacity)))
            if lesson.title in {"Controller Setup & Basics", "Beat Making Workshop", "Welcome Back Open Decks"}:
                attendees = [demo] + attendees[:-1]
            for student in attendees:
                past_signups.append(ClassSignup(student=student, lesson=lesson, status="confirmed",
                                                signed_up_at=lesson.created_at + timedelta(hours=self.rng.randint(2, 72))))
        ClassSignup.objects.bulk_create(past_signups)

    def create_class_requests(self):
        s, t = self.students, self.teachers
        rows = [
            # (student, teacher, days ahead, hour, minutes, skill, location, equipment, description, status, created days ago)
            (s["demo_student"], t["prod_nina"], 9, 16, 60, "Beginner", "Clemons Library, Robertson Media Center", "Laptop with FL Studio",
             "Could we do a one-on-one mixing session? I have a beat I'm stuck on.", "pending", 1),
            (s["maya_c"], t["demo_teacher"], 6, 15, 60, "Intermediate", "Newcomb Hall, Room 481", "DDJ-FLX4",
             "I can't make the Thursday class. Could you do a make-up session on phrasing?", "pending", 2),
            (s["ethan_p"], t["demo_teacher"], 12, 18, 90, "Beginner", "Brooks Hall Commons", "",
             "A few of us from my dorm want a beginner session together (4 people).", "pending", 0),
            (s["zara_k"], t["dj_marcus"], 8, 17, 60, "Beginner", "Old Cabell Hall B012", "Turntables",
             "Extra scratch practice before the routines class?", "pending", 3),
            (s["demo_student"], t["demo_teacher"], -4, 18, 60, "Beginner", "Newcomb Hall, Room 481", "",
             "Could I get some extra practice before the beatmatching class?", "accepted", 9),
            (s["kwame_a"], t["prod_leo"], -6, 19, 90, "Intermediate", "Rice Hall 130", "SP-404",
             "Would love a session on resampling.", "accepted", 12),
            (s["imani_w"], t["demo_teacher"], -2, 21, 60, "Advanced", "Newcomb Hall Ballroom", "CDJs",
             "Could we practice on the CDJs late Friday?", "denied", 8),
            (s["noah_g"], t["dj_priya"], -3, 16, 60, "Intermediate", "Student Activities Building, Studio 2", "",
             "Blending practice session?", "accepted", 7),
        ]
        for student, dj, days, hour, minutes, skill, loc, equip, desc, status, ago in rows:
            start = self.at(days, hour)
            created = self.now - timedelta(days=ago, hours=self.rng.randint(1, 10))
            ClassRequest(
                student=student, dj=dj, requested_start_time=start, requested_end_time=start + timedelta(minutes=minutes),
                requested_skill_level=skill, requested_location=loc, requested_equipment=equip, description=desc,
                status=status, created_at=created,
                responded_at=None if status == "pending" else created + timedelta(hours=self.rng.randint(2, 30)),
            ).save()

    def create_role_requests(self):
        reviewer = User.objects.filter(profile__role="admin_user").order_by("pk").first()
        pending = [
            ("chloe_d", "teacher", "I've been DJing house parties for two years and would love to help teach beginners."),
            ("jalen_r", "producer", "I produce beats in FL Studio and want to run a sampling workshop."),
        ]
        for username, role, why in pending:
            RoleChangeRequest.objects.create(profile=self.students[username].profile, requested_role=role, explanation=why)
        for username, role in [("dj_priya", "teacher"), ("prod_leo", "producer")]:
            req = RoleChangeRequest.objects.create(profile=self.teachers[username].profile, requested_role=role,
                                                   explanation="Experienced and want to teach this semester.",
                                                   status="approved", reviewer=reviewer)
            RoleChangeRequest.objects.filter(pk=req.pk).update(
                submitted_at=self.now - timedelta(days=35), reviewed_at=self.now - timedelta(days=34))

    def create_messages(self):
        everyone = {**self.teachers, **self.students}
        for a, b, lines in CONVERSATIONS:
            ua, ub = everyone[a], everyone[b]
            t = self.now - timedelta(days=self.rng.randint(1, 10), hours=self.rng.randint(0, 12))
            for i, text in enumerate(lines):
                sender, recipient = (ua, ub) if i % 2 == 0 else (ub, ua)
                t += timedelta(minutes=self.rng.randint(3, 240))
                if t > self.now:
                    t = self.now - timedelta(minutes=len(lines) - i)
                msg = Message.objects.create(sender=sender, recipient=recipient, content=text)
                # The last message of a thread is left unread so the demo inboxes show new activity.
                Message.objects.filter(pk=msg.pk).update(timestamp=t, is_read=i < len(lines) - 1)
