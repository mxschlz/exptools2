from psychopy.visual import Circle, TextStim, Rect


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
