from psychopy.visual import Circle, TextStim


def create_circle_fixation(win, radius=0.1, color=(1, 1, 1),
                           edges=100, **kwargs):
    """ Creates a circle fixation dot with sensible defaults. """
    return Circle(win, radius=radius, color=color, edges=edges, **kwargs)


def create_fixation_cross(win, text="+", color=(1, 1, 1), height=0.1, pos=(0, 0), **kwargs):
    return TextStim(win, pos=pos, color=color, height=height, text=text, **kwargs)
