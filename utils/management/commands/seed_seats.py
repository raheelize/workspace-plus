from django.core.management.base import BaseCommand
# Assuming your app is named 'seats_app' and your model is named 'Seat'
from seats_app.models import Seat 

class Command(BaseCommand):
    help = "Seed initial office seat layout from the provided visual map."

    def handle(self, *args, **options):
        # Optional: clear existing seats before seeding
        Seat.objects.all().delete()

        # Coordinates are approximated based on the visual layout in the image
        # The map spans roughly 800px wide by 700px high.
        # NOTE: space_id=1 has been added to resolve the IntegrityError,
        # assuming there is a Space/Office object with ID 1 already created.
        seats_data = [
            # --- Top Wall/Individual Seats ---
            {"code": "MA", "x": 80, "y": 120, "space_id": 1, 'is_reservable' : False},
            {"code": "TA", "x": 80, "y": 180, "space_id": 1, 'is_reservable' : False},
            {"code": "UF", "x": 280, "y": 50, "space_id": 1, 'is_reservable' : False},  # Upper front center left
            {"code": "FZ", "x": 420, "y": 50, "space_id": 1, 'is_reservable' : False},  # Upper front center right
            {"code": "URB", "x": 650, "y": 120, "space_id": 1, 'is_reservable' : False}, # Upper right back
            {"code": "AG", "x": 650, "y": 180, "space_id": 1, 'is_reservable' : False},

            # --- Top-Left Cluster (TL) ---
            {"code": "TL1", "x": 180, "y": 240, "space_id": 1},
            {"code": "TL2", "x": 180, "y": 300, "space_id": 1},
            {"code": "TL3", "x": 180, "y": 360, "space_id": 1},
            {"code": "TL4", "x": 280, "y": 240, "space_id": 1},
            {"code": "TL5", "x": 280, "y": 300, "space_id": 1},
            {"code": "TL6", "x": 280, "y": 360, "space_id": 1},
            {"code": "TL7", "x": 280, "y": 420, "space_id": 1},

            # --- Top-Center Cluster (MH, TC) ---
            {"code": "MH", "x": 380, "y": 240, "space_id": 1},
            {"code": "TC1", "x": 380, "y": 300, "space_id": 1},
            {"code": "TC2", "x": 380, "y": 360, "space_id": 1},
            {"code": "TC3", "x": 380, "y": 420, "space_id": 1},
            {"code": "TC4", "x": 380, "y": 480, "space_id": 1},
            
            {"code": "TC5", "x": 480, "y": 240, "space_id": 1},
            {"code": "TC6", "x": 480, "y": 300, "space_id": 1},
            {"code": "TC7", "x": 480, "y": 360, "space_id": 1},
            {"code": "TC8", "x": 480, "y": 420, "space_id": 1},

            # --- Top-Right Cluster (TR, HR, RG) ---
            {"code": "TR1", "x": 680, "y": 240, "space_id": 1},
            {"code": "TR2", "x": 680, "y": 300, "space_id": 1},
            {"code": "HR", "x": 680, "y": 360, "space_id": 1},
            {"code": "RG", "x": 680, "y": 420, "space_id": 1},

            # --- Bottom-Left Wall & Cluster (WA, KSK, BL) ---
            {"code": "WA", "x": 80, "y": 560, "space_id": 1},
            {"code": "KSK", "x": 80, "y": 620, "space_id": 1},
            
            {"code": "BL1", "x": 200, "y": 540, "space_id": 1},
            {"code": "BL2", "x": 300, "y": 540, "space_id": 1},
            {"code": "BL3", "x": 400, "y": 540, "space_id": 1},
            
            {"code": "BL4", "x": 200, "y": 600, "space_id": 1},
            {"code": "BL5", "x": 300, "y": 600, "space_id": 1},
            {"code": "BL6", "x": 400, "y": 600, "space_id": 1},

            {"code": "BL7", "x": 200, "y": 660, "space_id": 1},
            {"code": "BL8", "x": 300, "y": 660, "space_id": 1},
            {"code": "BL9", "x": 400, "y": 660, "space_id": 1},

            # --- Bottom-Center Cluster (BC) ---
            {"code": "BC4", "x": 560, "y": 540, "space_id": 1},
            {"code": "BC2", "x": 560, "y": 600, "space_id": 1},
            {"code": "BC1", "x": 490, "y": 660, "space_id": 1},
            {"code": "BC3", "x": 630, "y": 660, "space_id": 1},

            # --- Bottom-Right Seats (BR, WR, HRZ) ---
            {"code": "BR1", "x": 730, "y": 540, "space_id": 1},
            {"code": "BR2", "x": 730, "y": 600, "space_id": 1},
            {"code": "WR", "x": 670, "y": 660, "space_id": 1},
            {"code": "HRZ", "x": 770, "y": 660, "space_id": 1},
        ]

        # Use bulk_create for efficient database insertion
        Seat.objects.bulk_create([Seat(**seat) for seat in seats_data])

        self.stdout.write(self.style.SUCCESS(f"✅ Seeded {len(seats_data)} seats successfully based on the provided layout."))
