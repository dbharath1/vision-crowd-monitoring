import math
from collections import Counter

import numpy as np


class CrowdDescriptorService:
    """
    Calculates crowd-level descriptors from tracked
    people and their movement information.

    Descriptors:
        - Irregularity
        - Sparsity
        - Randomness
        - Volatility

    These are operational implementations for the system.
    They should not be claimed as an exact reproduction of
    the base paper unless the paper's mathematical definitions
    are explicitly available and matched.
    """

    def calculate(
        self,
        tracks: list[dict],
        movement_results: dict[int, dict],
        frame_width: int,
        frame_height: int,
    ) -> dict:

        if frame_width <= 0 or frame_height <= 0:
            raise ValueError(
                "Frame dimensions must be greater than zero."
            )

        if not tracks:
            return {
                "irregularity": 0.0,
                "sparsity": 0.0,
                "randomness": 0.0,
                "volatility": 0.0,
                "person_count": 0,
            }

        centers = np.array(
            [
                track["center"]
                for track in tracks
            ],
            dtype=float,
        )

        # -------------------------------------------------
        # 1. SPARSITY
        # -------------------------------------------------
        #
        # Measures how spread out people are relative
        # to the available image area.
        #
        # Larger average nearest-neighbour distance
        # indicates greater spatial separation.
        # -------------------------------------------------

        sparsity = self._calculate_sparsity(
            centers,
            frame_width,
            frame_height,
        )

        # -------------------------------------------------
        # 2. RANDOMNESS
        # -------------------------------------------------
        #
        # Measures diversity of movement directions.
        # Entropy is used so that:
        #
        # one dominant direction -> lower randomness
        # many different directions -> higher randomness
        # -------------------------------------------------

        randomness = self._calculate_randomness(
            tracks,
            movement_results,
        )

        # -------------------------------------------------
        # 3. IRREGULARITY
        # -------------------------------------------------
        #
        # Measures variation in movement magnitude.
        # If everyone has similar movement, irregularity
        # is lower.
        #
        # If movement varies significantly between people,
        # irregularity increases.
        # -------------------------------------------------

        irregularity = self._calculate_irregularity(
            tracks,
            movement_results,
        )

        # -------------------------------------------------
        # 4. VOLATILITY
        # -------------------------------------------------
        #
        # Measures variation in movement direction.
        #
        # Different directions among nearby people produce
        # greater volatility.
        # -------------------------------------------------

        volatility = self._calculate_volatility(
            tracks,
            movement_results,
        )

        return {
            "irregularity": float(irregularity),
            "sparsity": float(sparsity),
            "randomness": float(randomness),
            "volatility": float(volatility),
            "person_count": len(tracks),
        }

    # =====================================================
    # SPARSITY
    # =====================================================

    def _calculate_sparsity(
        self,
        centers: np.ndarray,
        frame_width: int,
        frame_height: int,
    ) -> float:

        number_of_people = len(centers)

        if number_of_people <= 1:
            return 1.0

        nearest_distances = []

        for i in range(number_of_people):

            distances = []

            for j in range(number_of_people):

                if i == j:
                    continue

                distance = math.sqrt(
                    (
                        centers[i][0]
                        - centers[j][0]
                    ) ** 2
                    +
                    (
                        centers[i][1]
                        - centers[j][1]
                    ) ** 2
                )

                distances.append(distance)

            if distances:
                nearest_distances.append(
                    min(distances)
                )

        if not nearest_distances:
            return 0.0

        average_nearest_distance = (
            sum(nearest_distances)
            / len(nearest_distances)
        )

        # Normalize using image diagonal.
        diagonal = math.sqrt(
            frame_width ** 2
            +
            frame_height ** 2
        )

        if diagonal == 0:
            return 0.0

        sparsity = (
            average_nearest_distance
            / diagonal
        )

        return min(max(sparsity, 0.0), 1.0)

    # =====================================================
    # RANDOMNESS
    # =====================================================

    def _calculate_randomness(
        self,
        tracks: list[dict],
        movement_results: dict[int, dict],
    ) -> float:

        directions = []

        for track in tracks:

            track_id = int(
                track["track_id"]
            )

            movement = movement_results.get(
                track_id
            )

            if not movement:
                continue

            direction = movement.get(
                "direction"
            )

            if direction in (
                None,
                "UNKNOWN",
            ):
                continue

            directions.append(direction)

        if len(directions) <= 1:
            return 0.0

        counts = Counter(directions)

        total = len(directions)

        entropy = 0.0

        for count in counts.values():

            probability = count / total

            if probability > 0:
                entropy -= (
                    probability
                    * math.log2(probability)
                )

        possible_directions = 8

        maximum_entropy = math.log2(
            possible_directions
        )

        if maximum_entropy == 0:
            return 0.0

        randomness = (
            entropy / maximum_entropy
        )

        return min(
            max(randomness, 0.0),
            1.0,
        )

    # =====================================================
    # IRREGULARITY
    # =====================================================

    def _calculate_irregularity(
        self,
        tracks: list[dict],
        movement_results: dict[int, dict],
    ) -> float:

        displacements = []

        for track in tracks:

            track_id = int(
                track["track_id"]
            )

            movement = movement_results.get(
                track_id
            )

            if not movement:
                continue

            displacement = movement.get(
                "displacement"
            )

            if displacement is not None:
                displacements.append(
                    float(displacement)
                )

        if len(displacements) <= 1:
            return 0.0

        values = np.array(
            displacements,
            dtype=float,
        )

        mean_value = np.mean(values)

        if mean_value <= 0:
            return 0.0

        standard_deviation = np.std(values)

        coefficient_of_variation = (
            standard_deviation
            / mean_value
        )

        # Normalize using a bounded transformation.
        irregularity = (
            coefficient_of_variation
            /
            (1.0 + coefficient_of_variation)
        )

        return min(
            max(float(irregularity), 0.0),
            1.0,
        )

    # =====================================================
    # VOLATILITY
    # =====================================================

    def _calculate_volatility(
        self,
        tracks: list[dict],
        movement_results: dict[int, dict],
    ) -> float:

        direction_vectors = []

        direction_mapping = {
            "RIGHT": (1.0, 0.0),
            "UP_RIGHT": (1.0, -1.0),
            "UP": (0.0, -1.0),
            "UP_LEFT": (-1.0, -1.0),
            "LEFT": (-1.0, 0.0),
            "DOWN_LEFT": (-1.0, 1.0),
            "DOWN": (0.0, 1.0),
            "DOWN_RIGHT": (1.0, 1.0),
        }

        for track in tracks:

            track_id = int(
                track["track_id"]
            )

            movement = movement_results.get(
                track_id
            )

            if not movement:
                continue

            direction = movement.get(
                "direction"
            )

            vector = direction_mapping.get(
                direction
            )

            if vector is not None:
                direction_vectors.append(
                    vector
                )

        if len(direction_vectors) <= 1:
            return 0.0

        vectors = np.array(
            direction_vectors,
            dtype=float,
        )

        mean_vector = np.mean(
            vectors,
            axis=0,
        )

        # Magnitude of mean direction.
        mean_magnitude = math.sqrt(
            mean_vector[0] ** 2
            +
            mean_vector[1] ** 2
        )

        # If all people move in the same direction,
        # mean vector magnitude approaches 1.
        #
        # If movement directions are highly diverse,
        # the mean vector approaches 0.
        #
        # Therefore volatility is the inverse.
        volatility = (
            1.0 - mean_magnitude
        )

        return min(
            max(float(volatility), 0.0),
            1.0,
        )