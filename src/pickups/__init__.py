from .pickup import Pickup
from .health_pickup import HealthPickup
from .ammo_pickup import AmmoPickup
from .shield_pickup import ShieldPickup


PICKUP_TYPES = {
    HealthPickup.PICKUP_NAME: HealthPickup,
    AmmoPickup.PICKUP_NAME: AmmoPickup,
    ShieldPickup.PICKUP_NAME: ShieldPickup,
}


def create_pickup(pickup_type, x, y):
    pickup_class = PICKUP_TYPES.get(pickup_type)

    if pickup_class is None:
        raise ValueError(f"Unknown pickup type: {pickup_type}")

    return pickup_class(x, y)