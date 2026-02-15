import random
import copy
import statistics
import time


class Scheduler:

    def __init__(self, data, weights):

        self.days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
        self.slots_per_day = 5

        self.courses = data["courses"]
        self.rooms = data["rooms"]
        self.teacher_unavailability = data["teacher_unavailability"]

        self.weights = weights

        self.reset()

    # ---------------------------------------------------
    # RESET STRUCTURES
    # ---------------------------------------------------

    def reset(self):

        self.timetable = {
            day: {
                slot: {room: None for room in self.rooms}
                for slot in range(1, self.slots_per_day + 1)
            }
            for day in self.days
        }

        self.teacher_daily_load = {day: {} for day in self.days}
        self.batch_slot_usage = {
            day: {slot: {} for slot in range(1, self.slots_per_day + 1)}
            for day in self.days
        }

        self.day_load = {day: 0 for day in self.days}

    # ---------------------------------------------------
    # HARD CONSTRAINTS
    # ---------------------------------------------------

    def is_valid(self, day, slot, room, course):

        teacher = course["teacher"]
        batch = course["batch"]
        course_type = course["type"]
        room_type = self.rooms[room]["type"]

        # Teacher unavailable
        if teacher in self.teacher_unavailability:
            if (day, slot) in self.teacher_unavailability[teacher]:
                return False

        # Room occupied
        if self.timetable[day][slot][room] is not None:
            return False

        # Lab/Project rule
        if course_type in ["lab", "project"] and room_type != "lab":
            return False

        if course_type == "theory" and room_type == "lab":
            return False

        # Teacher clash
        for r in self.rooms:
            assigned = self.timetable[day][slot][r]
            if assigned and assigned["teacher"] == teacher:
                return False

        # Batch clash
        if batch in self.batch_slot_usage[day][slot]:
            return False

        # Teacher max 3 per day
        if self.teacher_daily_load[day].get(teacher, 0) >= 3:
            return False

        return True

    # ---------------------------------------------------
    # ASSIGN
    # ---------------------------------------------------

    def assign(self, day, slot, room, course):

        teacher = course["teacher"]
        batch = course["batch"]

        self.timetable[day][slot][room] = course

        self.teacher_daily_load[day][teacher] = \
            self.teacher_daily_load[day].get(teacher, 0) + 1

        self.batch_slot_usage[day][slot][batch] = True

        self.day_load[day] += 1

    # ---------------------------------------------------
    # CSP MODE
    # ---------------------------------------------------

    def run_csp(self):

        self.reset()

        # for course in self.courses:
        sorted_courses = sorted(self.courses, key=lambda x: x["hours"], reverse=True)

        for course in sorted_courses:


            remaining_hours = course["hours"]
            duration = 2 if course["type"] in ["lab", "project"] else 1

            while remaining_hours > 0:

                placed = False

                for day in self.days:
                    for slot in range(1, self.slots_per_day + 1):

                        if slot + duration - 1 > self.slots_per_day:
                            continue

                        for room in self.rooms:

                            valid = True
                            for d in range(duration):
                                if not self.is_valid(day, slot + d, room, course):
                                    valid = False
                                    break

                            if valid:
                                for d in range(duration):
                                    self.assign(day, slot + d, room, course)

                                remaining_hours -= duration
                                placed = True
                                break

                        if placed:
                            break
                    if placed:
                        break

                if not placed:
                    # No more valid placement possible
                    break

        return self.timetable

    # ---------------------------------------------------
    # OPTIMIZER MODE
    # ---------------------------------------------------

    def run_optimizer(self):

        best_score = -999999
        best_table = None

        for _ in range(5):

            self.reset()
            shuffled = self.courses[:]
            random.shuffle(shuffled)

            for course in shuffled:

                remaining_hours = course["hours"]
                duration = 2 if course["type"] in ["lab", "project"] else 1

                attempts = 0

                while remaining_hours > 0 and attempts < 60:

                    day = random.choice(self.days)
                    slot = random.randint(1, self.slots_per_day)

                    if slot + duration - 1 > self.slots_per_day:
                        attempts += 1
                        continue

                    room = random.choice(list(self.rooms.keys()))

                    valid = True
                    for d in range(duration):
                        if not self.is_valid(day, slot + d, room, course):
                            valid = False
                            break

                    if valid:
                        for d in range(duration):
                            self.assign(day, slot + d, room, course)

                        remaining_hours -= duration
                    else:
                        attempts += 1

            score = self.score()

            if score > best_score:
                best_score = score
                best_table = copy.deepcopy(self.timetable)

        return best_table


    # ---------------------------------------------------
    # HYBRID MODE
    # ---------------------------------------------------

    def run_hybrid(self):

        self.run_csp()
        base = copy.deepcopy(self.timetable)

        improved = self.run_optimizer()

        return improved if improved else base

    # ---------------------------------------------------
    # SOFT SCORING
    # ---------------------------------------------------

    def score(self):

        loads = list(self.day_load.values())
        imbalance = statistics.pstdev(loads)

        total_sessions = sum(loads)

        teacher_loads = []
        for day in self.teacher_daily_load:
            teacher_loads.extend(self.teacher_daily_load[day].values())

        teacher_variance = statistics.pstdev(teacher_loads) if teacher_loads else 0

        room_usage = []
        for day in self.days:
            for slot in range(1, self.slots_per_day + 1):
                count = sum(1 for r in self.rooms if self.timetable[day][slot][r])
                room_usage.append(count)

        room_balance = statistics.pstdev(room_usage) if room_usage else 0

        return (
            total_sessions
            - self.weights["day_balance"] * imbalance
            - self.weights["teacher_balance"] * teacher_variance
            - self.weights["room_balance"] * room_balance
        )

    # ---------------------------------------------------
    # METRICS
    # ---------------------------------------------------

    def evaluate(self):

        teacher_summary = {}
        room_summary = {room: 0 for room in self.rooms}
        day_summary = self.day_load.copy()

        total_sessions = 0

        for day in self.days:
            for slot in range(1, self.slots_per_day + 1):
                for room in self.rooms:
                    course = self.timetable[day][slot][room]
                    if course:
                        total_sessions += 1
                        room_summary[room] += 1
                        teacher = course["teacher"]
                        teacher_summary[teacher] = \
                            teacher_summary.get(teacher, 0) + 1

        return total_sessions, teacher_summary, room_summary, day_summary

    def course_coverage(self):

        coverage = {}

        # Count scheduled occurrences
        scheduled_count = {}

        for day in self.days:
            for slot in range(1, self.slots_per_day + 1):
                for room in self.rooms:
                    course = self.timetable[day][slot][room]
                    if course:
                        code = course["code"]
                        scheduled_count[code] = scheduled_count.get(code, 0) + 1

        # Compare with required
        for course in self.courses:
            code = course["code"]
            required = course["hours"]
            scheduled = scheduled_count.get(code, 0)

            coverage[code] = {
                "required": required,
                "scheduled": scheduled,
                "batch": course["batch"],
                "status": "OK" if scheduled >= required else "MISSING"
            }

        return coverage

    def feasibility_analysis(self):

        warnings = []

        # -----------------------------
        # 1️⃣ Total Weekly Capacity
        # -----------------------------
        total_slots = len(self.days) * self.slots_per_day * len(self.rooms)
        total_required = sum(course["hours"] for course in self.courses)

        if total_required > total_slots:
            warnings.append(
                f"Total required hours ({total_required}) exceed total available slots ({total_slots})"
            )

        # -----------------------------
        # 2️⃣ Lab Capacity Check
        # -----------------------------
        lab_rooms = [r for r in self.rooms if self.rooms[r]["type"] == "lab"]
        lab_capacity = len(self.days) * self.slots_per_day * len(lab_rooms)

        total_lab_required = sum(
            course["hours"] for course in self.courses
            if course["type"] in ["lab", "project"]
        )

        if total_lab_required > lab_capacity:
            warnings.append(
                f"Lab hours required ({total_lab_required}) exceed lab capacity ({lab_capacity})"
            )

        # -----------------------------
        # 3️⃣ Teacher Weekly Load Check
        # -----------------------------
        teacher_required = {}

        for course in self.courses:
            teacher_required[course["teacher"]] = \
                teacher_required.get(course["teacher"], 0) + course["hours"]

        max_weekly = len(self.days) * 3  # 3 per day limit

        for teacher, hours in teacher_required.items():
            if hours > max_weekly:
                warnings.append(
                    f"Teacher {teacher} exceeds weekly limit ({hours} > {max_weekly})"
                )

        # -----------------------------
        # 4️⃣ Batch Weekly Load Check
        # -----------------------------
        batch_required = {}

        for course in self.courses:
            batch_required[course["batch"]] = \
                batch_required.get(course["batch"], 0) + course["hours"]

        max_batch_weekly = len(self.days) * self.slots_per_day

        for batch, hours in batch_required.items():
            if hours > max_batch_weekly:
                warnings.append(
                    f"Batch {batch} exceeds weekly slot capacity ({hours} > {max_batch_weekly})"
                )

        return warnings

# ---------------------------------------------------
# MAIN ENTRY
# ---------------------------------------------------

def generate_timetable(data, weights, mode="hybrid"):

    start = time.time()

    scheduler = Scheduler(data, weights)

    if mode == "csp":
        timetable = scheduler.run_csp()
    elif mode == "optimizer":
        timetable = scheduler.run_optimizer()
    else:
        timetable = scheduler.run_hybrid()

    execution_time = round(time.time() - start, 4)

    total_sessions, teacher_summary, room_summary, day_summary = \
        scheduler.evaluate()

    coverage = scheduler.course_coverage()
    warnings = scheduler.feasibility_analysis()


    # ------------------------------------
    # ADVANCED AI EVALUATION METRICS
    # ------------------------------------

    import statistics

    # 1️⃣ Room Utilization %
    total_possible = len(scheduler.days) * scheduler.slots_per_day * len(scheduler.rooms)
    room_utilization_percentage = round((total_sessions / total_possible) * 100, 2)

    # 2️⃣ Teacher Fairness Score (lower variance = better)
    teacher_loads = list(teacher_summary.values())
    if teacher_loads:
        teacher_variance = statistics.pstdev(teacher_loads)
        teacher_fairness_score = round(100 - (teacher_variance * 10), 2)
        teacher_fairness_score = max(0, min(100, teacher_fairness_score))
    else:
        teacher_fairness_score = 0

    # 3️⃣ Day Balance Score
    day_loads = list(day_summary.values())
    if day_loads:
        day_variance = statistics.pstdev(day_loads)
        day_balance_score = round(100 - (day_variance * 10), 2)
        day_balance_score = max(0, min(100, day_balance_score))
    else:
        day_balance_score = 0

    # 4️⃣ Global Efficiency Score
    efficiency_score = round(
        (room_utilization_percentage * 0.4) +
        (teacher_fairness_score * 0.3) +
        (day_balance_score * 0.3),
    2)


    metrics = {
    "total_sessions": total_sessions,
    "execution_time": execution_time,
    "room_utilization": room_utilization_percentage,
    "teacher_fairness": teacher_fairness_score,
    "day_balance": day_balance_score,
    "efficiency_score": efficiency_score
}


    return timetable, metrics, teacher_summary, room_summary, day_summary, coverage, warnings
