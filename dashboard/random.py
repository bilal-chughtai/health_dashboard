import random
import math
from datetime import datetime, timedelta
from typing import List
import numpy as np
from .models import DailyData, OuraData, CronometerData, GarminData, ManualData

def generate_random_data(start_date: datetime, end_date: datetime) -> List[DailyData]:
    """Generate realistic synthetic health data with correlations and temporal patterns"""
    
    # Calculate date range
    days = (end_date - start_date).days + 1
    dates = [start_date + timedelta(days=i) for i in range(days)]
    
    # Initialize person's baseline characteristics
    base_fitness = random.uniform(0.4, 0.8)  # Overall fitness level
    base_sleep_quality = random.uniform(0.6, 0.9)  # Sleep quality tendency
    base_weight = random.uniform(72, 85)  # Starting weight
    base_rhr = int(random.uniform(45, 55))  # Base resting heart rate
    base_vo2 = random.uniform(48, 58)  # VO2 max (changes very slowly)
    
    # Training periodization - create weekly load cycles
    weekly_loads = []
    for week_num in range(math.ceil(days / 7)):
        # 3 weeks build, 1 week recovery pattern
        if week_num % 4 == 3:
            weekly_loads.append(0.4)  # Recovery week
        else:
            weekly_loads.append(random.uniform(0.7, 1.0))  # Build weeks
    
    # VO2 max improvement over time (slow linear progression)
    vo2_start = base_vo2
    vo2_end = base_vo2 + random.uniform(2, 6)  # 2-6 point improvement over time period
    
    daily_data = []
    prev_sleep_score = 80
    prev_hrv = 60
    current_weight = base_weight
    weekly_run_km = 0  # Track weekly running volume
    weekly_lifts = 0   # Track weekly lifting sessions
    
    for i, date in enumerate(dates):
        day_of_week = date.weekday()  # 0=Monday, 6=Sunday
        week_num = i // 7
        day_in_week = i % 7
        weekly_load = weekly_loads[min(week_num, len(weekly_loads) - 1)]
        
        # Reset weekly counters on Monday
        if day_of_week == 0:
            weekly_run_km = 0
            weekly_lifts = 0
        
        # Calculate current VO2 max (linear improvement over time)
        progress = i / max(1, days - 1)  # 0 to 1
        current_vo2 = vo2_start + (vo2_end - vo2_start) * progress
        
        # Weekend vs weekday patterns
        is_weekend = day_of_week >= 5
        sleep_modifier = 1.1 if is_weekend else 1.0
        activity_modifier = 0.8 if is_weekend else 1.0
        
        # Recovery factor based on previous day
        recovery_factor = (prev_sleep_score / 100 + prev_hrv / 100) / 2
        recovery_factor = max(0.6, min(1.2, recovery_factor))
        
        # Generate Oura data (always available - always wear ring)
        oura_data = None
        if True:  # Always available
            sleep_score = int(np.clip(
                random.gauss(80 + base_sleep_quality * 20 * sleep_modifier, 10),
                60, 100
            ))
            
            sleep_duration = np.clip(
                random.gauss(7.5 + (0.5 if is_weekend else 0), 0.8),
                6.0, 10.0
            )
            
            readiness_score = int(np.clip(
                random.gauss(80 + (sleep_score - 80) * 0.5, 8) * recovery_factor,
                60, 100
            ))
            
            activity_score = int(np.clip(
                random.gauss(80 + base_fitness * 15 * weekly_load * activity_modifier * recovery_factor, 8),
                60, 100
            ))
            
            steps = int(np.clip(
                random.gauss(8000 + 4000 * base_fitness * weekly_load * activity_modifier, 2000),
                2000, 25000
            ))
            
            sleep_hr = int(np.clip(
                base_rhr * random.uniform(0.85, 1.05),
                35, 60
            ))
            
            sleep_lowest_hr = int(sleep_hr * random.uniform(0.85, 0.95))
            
            sleep_hrv = np.clip(
                random.gauss(50 + base_fitness * 30 + (sleep_score - 70) * 0.5, 8),
                30, 90
            )
            
            oura_data = OuraData(
                source="oura",
                date=date,
                sleep_score=sleep_score,
                sleep_duration_hours=round(sleep_duration, 1),
                readiness_score=readiness_score,
                activity_score=activity_score,
                steps=steps,
                sleep_heart_rate=round(sleep_hr, 1),
                sleep_lowest_heart_rate=sleep_lowest_hr,
                sleep_hrv=round(sleep_hrv, 1)
            )
            
            prev_sleep_score = sleep_score
            prev_hrv = sleep_hrv
        
        # Generate Cronometer data (nutrition) - 5% missing
        cronometer_data = None
        if random.random() > 0.05:  # 95% tracking compliance
            base_calories = 2200 + base_fitness * 400
            calories = np.clip(
                random.gauss(base_calories + (200 if is_weekend else 0), 200),
                1200, 3500
            )
            
            # Protein correlates with training load
            protein = np.clip(
                random.gauss(100 + weekly_load * 50, 20),
                60, 200
            )
            
            carbs = np.clip(
                random.gauss(200 + weekly_load * 80, 40),
                100, 400
            )
            
            fat = np.clip(
                random.gauss(80 + weekly_load * 20, 15),
                40, 150
            )
            
            # Saturated fat is typically 30-40% of total fat
            saturated_fat_ratio = random.uniform(0.30, 0.40)
            saturated_fat = np.clip(
                fat * saturated_fat_ratio,
                10, 60  # Reasonable range for saturated fat
            )
            
            cronometer_data = CronometerData(
                source="cronometer",
                date=date,
                calories=round(calories),
                protein=round(protein, 1),
                carbs=round(carbs, 1),
                fat=round(fat, 1),
                saturated_fat=round(saturated_fat, 1)
            )
        
        # Generate Garmin running data (never Strava)
        garmin_data = None
        
        # Running strategy: aim for 30-50km per week, 4-6 runs per week
        target_weekly_km = random.uniform(30, 50)
        runs_per_week = random.randint(4, 6)
        
        # Don't run if we've already hit weekly targets or too many runs
        weekly_runs_so_far = sum(1 for j in range(max(0, i-6), i) if j < len(daily_data) and daily_data[j].garmin and daily_data[j].garmin.total_distance_km)
        
        run_probability = 0.8 if (weekly_run_km < target_weekly_km * 0.8 and weekly_runs_so_far < runs_per_week) else 0.1
        run_probability *= recovery_factor  # Recovery affects running
        
        if random.random() < run_probability:
            # Variable run distances to hit weekly target
            remaining_km = max(3, target_weekly_km - weekly_run_km)
            remaining_runs = max(1, runs_per_week - weekly_runs_so_far)
            avg_distance = remaining_km / remaining_runs
            
            distance = np.clip(
                random.gauss(avg_distance, 2),
                3, 15  # 3km minimum, 15km max
            )
            
            pace_per_km = 4.5 + (1 - base_fitness) * 1.5  # minutes per km
            duration = distance * pace_per_km / 60  # hours
            
            weekly_run_km += distance
            
            # Base daily steps + running steps
            base_daily_steps = int(random.gauss(6000, 1500))
            running_steps = int(distance * 1400)  # ~1400 steps per km
            total_steps = base_daily_steps + running_steps
            
            garmin_data = GarminData(
                source="garmin",
                date=date,
                total_distance_km=round(distance, 1),
                total_duration_hours=round(duration, 2),
                steps=total_steps,
                resting_heart_rate=base_rhr + random.randint(-3, 3),
                hrv=int(prev_hrv + random.gauss(0, 5)) if prev_hrv else None,
                vo2_max=round(current_vo2 + random.gauss(0, 0.5), 1)  # Slow improvement with noise
            )
        else:
            # Non-running day - just regular daily steps
            if random.random() > 0.1:  # Sometimes Garmin data even without runs
                total_steps = int(np.clip(
                    random.gauss(8000, 2000),
                    3000, 15000
                ))
                
                garmin_data = GarminData(
                    source="garmin",
                    date=date,
                    total_distance_km=None,
                    total_duration_hours=None,
                    steps=total_steps,
                    resting_heart_rate=base_rhr + random.randint(-3, 3),
                    hrv=int(prev_hrv + random.gauss(0, 5)) if prev_hrv else None,
                    vo2_max=round(current_vo2 + random.gauss(0, 0.5), 1)
                )
        
        # Generate manual data
        manual_data = None
        
        # Weight tracking (slow random walk)
        if random.random() > 0.3:  # 70% compliance
            weight_change = random.gauss(0, 0.1)  # Small daily fluctuations
            current_weight += weight_change
            current_weight = np.clip(current_weight, 70, 90)
        
        # Lifting pattern - aim for 3-5 times per week
        target_lifts_per_week = random.randint(3, 5)
        
        # Check how many lifts this week so far
        lifts_this_week = weekly_lifts
        
        # Higher probability early in week, lower if we've hit target
        if lifts_this_week < target_lifts_per_week:
            lift_probability = 0.7 * weekly_load * recovery_factor
        else:
            lift_probability = 0.1  # Occasional extra session
            
        # Don't lift on long run days usually
        if garmin_data and garmin_data.total_distance_km and garmin_data.total_distance_km > 10:
            lift_probability *= 0.3
            
        did_lift = random.random() < lift_probability
        if did_lift:
            weekly_lifts += 1
        
        if random.random() > 0.1:  # 90% tracking
            manual_data = ManualData(
                source="manual",
                date=date,
                bodyweight_kg=round(current_weight, 1),
                lift=did_lift
            )
        
        # Create daily data entry
        daily_entry = DailyData(
            date=date,
            oura=oura_data,
            cronometer=cronometer_data,
            strava=None,  # Never use Strava
            garmin=garmin_data,
            manual=manual_data
        )
        
        daily_data.append(daily_entry)
    
    return daily_data


# Example usage:
# start = datetime(2024, 1, 1)
# end = datetime(2024, 12, 31)
# synthetic_data = generate_random_data(start, end)