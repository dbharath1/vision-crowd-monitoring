from typing import Optional


class DensityService:
    """
    Calculates crowd density from actual tracked people.

    Density:
        people / monitored area
    """

    def calculate(
        self,
        tracks: list[dict],
        frame_width: int,
        frame_height: int,
        monitored_area: Optional[float] = None,
    ) -> dict:

        person_count = len(tracks)

        if monitored_area is None:
            area = float(frame_width * frame_height)
            area_unit = "pixel^2"
        else:
            area = float(monitored_area)

            if area <= 0:
                raise ValueError(
                    "Monitored area must be greater than zero."
                )

            area_unit = "configured_area"

        if area <= 0:
            raise ValueError(
                "Frame area must be greater than zero."
            )

        density = person_count / area

        density_per_100k_pixels = (
            person_count / area * 100000
            if area_unit == "pixel^2"
            else None
        )

        return {
            "person_count": person_count,
            "area": area,
            "density": float(density),
            "density_per_100k_pixels": (
                float(density_per_100k_pixels)
                if density_per_100k_pixels is not None
                else None
            ),
            "area_unit": area_unit,
            "frame_width": frame_width,
            "frame_height": frame_height,
        }