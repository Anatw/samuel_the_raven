from Servo import Mouth, HeadUpDown, HeadLeftRight, Wings, Body


class Movement():
    mouth = Mouth(
        pin_number=0,
        min_value=6200,
        max_value=9250,
        gesticulation_repetition=1
    )
    # For head up-down movement, lower numbers will turn down, higher numbers will turn up:
    head_ud = HeadUpDown(
        pin_number=1,
        min_value=4450,
        max_value=8400,
        gesticulation_repetition=4
    )
    head_rl = HeadLeftRight(
        pin_number=2,
        min_value=3300,
        max_value=7100,
        gesticulation_repetition=5
    )
    wings = Wings(
        pin_number=3,
        min_value=4600,
        max_value=5750,
        gesticulation_repetition=3
    )
    body = Body(
        pin_number=4,
        min_value=5000,
        max_value=6200,
        gesticulation_repetition=2
    )
