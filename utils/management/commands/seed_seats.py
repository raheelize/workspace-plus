from django.core.management.base import BaseCommand
from seats_app.models import Seat

class Command(BaseCommand):
    help = "Seed initial office seat layout"

    def handle(self, *args, **options):
        Seat.objects.all().delete()  # optional: clear existing

        seats_data = [
            # --- Top section (front) ---
            {"code": "T1", "x": 120, "y": 60},
            {"code": "T2", "x": 320, "y": 60},

            # --- Left column cluster ---
            {"code": "L1", "x": 60, "y": 180},
            {"code": "L2", "x": 60, "y": 240},
            {"code": "L3", "x": 60, "y": 300},
            {"code": "L4", "x": 60, "y": 360},

            # --- Left-middle cluster ---
            {"code": "LM1", "x": 160, "y": 180},
            {"code": "LM2", "x": 160, "y": 240},
            {"code": "LM3", "x": 160, "y": 300},
            {"code": "LM4", "x": 160, "y": 360},

            # --- Center cluster ---
            {"code": "C1", "x": 260, "y": 180},
            {"code": "C2", "x": 260, "y": 240},
            {"code": "C3", "x": 260, "y": 300},
            {"code": "C4", "x": 260, "y": 360},

            # --- Right cluster ---
            {"code": "R1", "x": 360, "y": 180},
            {"code": "R2", "x": 360, "y": 240},
            {"code": "R3", "x": 360, "y": 300},
            {"code": "R4", "x": 360, "y": 360},

            # --- Far right wall ---
            {"code": "RW1", "x": 460, "y": 180},
            {"code": "RW2", "x": 460, "y": 240},
            {"code": "RW3", "x": 460, "y": 300},
            {"code": "RW4", "x": 460, "y": 360},

            # --- Bottom clusters ---
            {"code": "B1", "x": 120, "y": 480},
            {"code": "B2", "x": 180, "y": 480},
            {"code": "B3", "x": 240, "y": 480},
            {"code": "B4", "x": 300, "y": 480},
            {"code": "B5", "x": 360, "y": 480},
            {"code": "B6", "x": 420, "y": 480},

            # --- Bottom right ---
            {"code": "BR1", "x": 480, "y": 480},
            {"code": "BR2", "x": 540, "y": 480},

            # --- Bottom left side ---
            {"code": "BL1", "x": 60, "y": 480},
            {"code": "BL2", "x": 60, "y": 540},
            {"code": "BL3", "x": 120, "y": 540},
            {"code": "BL4", "x": 180, "y": 540},

            # --- Side corner ---
            {"code": "S1", "x": 480, "y": 540},
            {"code": "S2", "x": 540, "y": 540},
            {"code": "S3", "x": 600, "y": 540},
            {"code": "S4", "x": 660, "y": 540},
        ]

        Seat.objects.bulk_create([Seat(**seat) for seat in seats_data])

        self.stdout.write(self.style.SUCCESS(f"✅ Seeded {len(seats_data)} seats successfully."))
