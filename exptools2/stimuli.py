from psychopy.visual import Circle, TextStim, Rect, ShapeStim


def create_circle_fixation(win, radius=0.1, color=(1, 1, 1),
                           edges=100, **kwargs):
    """ Creates a circle fixation dot with sensible defaults. """
    return Circle(win, radius=radius, color=color, edges=edges, **kwargs)


def create_fixation_cross(win, text="+", color=(1, 1, 1), height=1, pos=(0, 0), **kwargs):
    return TextStim(win, pos=pos, color=color, height=height, text=text, **kwargs)


def create_virtual_response_box(win, digits, size, units):

    # Visual stimuli for numpad digits
    digit_stimuli = []

    # Numpad box (frame)
    numpad_box = Rect(win, width=size, height=size, lineColor='black',
                      fillColor=None, units=units, name="Box_Border")  # Adjust colors as desired
    digit_stimuli.append(numpad_box)

    # Adjust font size to ensure it fits within the buttons
    font_size = min(size / 3, size / 4)  # Adjust the multiplier as needed

    for i, digit in enumerate(digits):
        row = i // 3
        col = i % 3

        # Simplified and improved centering logic
        x_pos = -size / 2 + (col + 0.5) * (size / 3)
        y_pos = size / 2 - (row + 0.5) * (size / 3)

        stimulus = TextStim(win, text=str(digit), pos=(x_pos, y_pos), height=font_size, name=f"Digit_{digit}")
        digit_stimuli.append(stimulus)
        # Print values for debugging
        print(f"Digit {digit}: x_pos={x_pos}, y_pos={y_pos}, font_size={font_size}")

    return digit_stimuli


def create_shape_stims(win, arrow_size=0.6, arrow_offset=1.0): # Default arrow_size increased
    """
    Creates the three arrow ShapeStim objects (left, up, right)
    and returns them in a list. Arrows are now larger by default
    and positioned further from the center, scaling with arrow_size.

    Args:
        win: The PsychoPy window object.
        arrow_size: Size of the arrows. Also influences their distance from center.

    Returns:
        A list containing the left, up, and right arrow ShapeStim objects.
    """
    # New vertices for a slightly longer arrow with a clear shaft and head.
    # Arrow points right, with tip at (0,0) and base at x=-0.5 in its local coordinates.
    # Total length = 0.5 units, max head width = 0.2 units.
    arrow_vertices = [
        (-0.5, 0.04),  # Top-left of shaft
        (-0.2, 0.04),  # Top-right of shaft (connects to head base)
        (-0.2, 0.1),   # Top-outer point of head base
        (0, 0),        # Tip of the arrow
        (-0.2, -0.1),  # Bottom-outer point of head base
        (-0.2, -0.04), # Bottom-right of shaft (connects to head base)
        (-0.5, -0.04)  # Bottom-left of shaft
    ]

    # Calculate position offset based on arrow_size to maintain separation
    position_offset = arrow_size * arrow_offset

    # Create the left arrow
    arrow_left = ShapeStim(win,
                           vertices=arrow_vertices,
                           fillColor='white',
                           lineColor='white',
                           size=arrow_size,
                           pos=(-position_offset, 0),
                           ori=180)  # 180 degrees for left

    # Create the up arrow
    arrow_up = ShapeStim(win,
                         vertices=arrow_vertices,
                         fillColor='white',
                         lineColor='white',
                         size=arrow_size,
                         pos=(0, position_offset),
                         ori=270)  # 270 degrees for up (points upwards)

    # Create the right arrow
    arrow_right = ShapeStim(win,
                            vertices=arrow_vertices,
                            fillColor='white',
                            lineColor='white',
                            size=arrow_size,
                            pos=(position_offset, 0),
                            ori=0)  # 0 degrees for right

    # Return the arrows in a list. Ensure the order matches your location indices (e.g., 0, 1, 2).
    # If your locations are 0=left, 1=up, 2=right, this order is correct.
    return [arrow_left, arrow_up, arrow_right]