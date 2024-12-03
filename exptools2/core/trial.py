import numpy as np
from psychopy import event
from psychopy import logging
import time

# TODO:
# - add port_log (like dict(phase=code)) to trial init


class Trial:
    """ Base class for Trial objects. """

    def __init__(self, session, trial_nr, phase_durations, phase_names=None,
                 parameters=None, timing='seconds', verbose=True, draw_each_frame=True):
        """ Initializes Trial objects.

        parameters
        ----------
        session : exptools Session object
            A Session object (needed for metadata)
        trial_nr: int
            Trial nr of trial
        phase_durations : array-like
            List/tuple/array with phase durations
        phase_names : array-like
            List/tuple/array with names for phases (only for logging),
            optional (if None, all are named 'stim')
        parameters : dict
            Dict of parameters that needs to be added to the log of this trial
        timing : str
            The "units" of the phase durations. Default is 'seconds', where we
            assume the phase-durations are in seconds. The other option is
            'frames', where the phase-"duration" refers to the number of frames.
        verbose : bool
            Whether to print extra output (mostly timing info)
        draw_each_frame : bool
            Whether to draw on each frame, or let the draw function decide when to flip the buffers.

        attributes
        ----------
        phase : int
            Current phase nr (starting for 0)
        exit_phase : bool
            Whether the current phase should be exited (set when calling
            session.stop_phase())
        last_resp : str
            Last response given (for convenience)
        """
        self.session = session
        self.trial_nr = trial_nr
        self.phase_durations = list(phase_durations)
        self.phase_names = phase_names
        self.parameters = dict() if parameters is None else parameters
        self.timing = timing
        self.verbose = verbose
        self.draw_each_frame = draw_each_frame

        self.start_trial = None
        self.exit_phase = False
        self.exit_trial = False
        self.n_phase = len(phase_durations)
        self.phase = 0
        self.last_resp = None
        self.last_resp_onset = None

        self._check_params()

    def _check_params(self):
        """ Checks whether parameters/settings are valid. """
        TIMING_OPTS = ['seconds', 'frames']
        if self.timing not in TIMING_OPTS:
            raise ValueError("Please set timing to one of %s" % (TIMING_OPTS,))

        if self.timing == 'frames':
            if not all([isinstance(dur, int) for dur in self.phase_durations]):
                raise ValueError("Durations should be integers when timing "
                                 "is set to 'frames'!")

    def draw(self):
        """ Should be implemented in child Class. """
        raise NotImplementedError

    def create_trial(self):
        """ Should be implemented in child Class. """
        raise NotImplementedError

    def log_phase_info(self, phase=None):
        """ Method passed to win.callonFlip, such that the
        onsets get logged *exactly* on the screen flip.

        Phase can be passed as an argument to log the onsets
        of phases that finish before a window flip (e.g.,
        phases with duration = 0, and are skipped on some
        trials).
        """
        onset = self.session.clock.getTime()

        if phase is None:
            phase = self.phase

        if phase == 0:
            self.start_trial = onset

            if self.verbose:
                print(f'Starting trial {self.trial_nr}')

        msg = f"\tPhase {phase} start: {onset:.5f}"

        if self.verbose:
            print(msg)

        # add to global log
        idx = self.session.global_log.shape[0]
        self.session.global_log.loc[idx, 'onset'] = onset
        self.session.global_log.loc[idx, 'trial_nr'] = self.trial_nr
        # print(phase)
        self.session.global_log.loc[idx, 'event_type'] = self.phase_names[phase]
        self.session.global_log.loc[idx, 'phase'] = phase
        self.session.global_log.loc[idx, 'nr_frames'] = self.session.nr_frames

        for param, val in self.parameters.items():  # add parameters to log
            if type(val) == np.ndarray or type(val) == list:
                for i, x in enumerate(val):
                    self.session.global_log.loc[idx, param+'_%4i'%i] = str(x) 
            else:       
                self.session.global_log.loc[idx, param] = val
        self.session.nr_frames = 0

    def stop_phase(self):
        """ Allows you to break out the drawing loop while the phase-duration
        has not completely passed (e.g., when a user pressed a button). """
        self.exit_phase = True

    def stop_trial(self):
        """ Allows you to break out of the trial while not completely finished """
        self.exit_trial = True

    def _log_event(self, event_type, response, t):
        """Helper function to log an event to the global log."""

        idx = self.session.global_log.shape[0]
        self.session.global_log.loc[idx, 'trial_nr'] = self.trial_nr
        self.session.global_log.loc[idx, 'onset'] = t
        self.session.global_log.loc[idx, 'event_type'] = event_type
        self.session.global_log.loc[idx, 'phase'] = self.phase
        self.session.global_log.loc[idx, 'response'] = response
        self.session.global_log.loc[idx, 'rt'] = t - self.start_trial

        for param, val in self.parameters.items():
            if isinstance(val, (np.ndarray, list)):
                for i, x in enumerate(val):
                    self.session.global_log.loc[idx, param + '_%04i' % i] = x
            else:
                self.session.global_log.loc[idx, param] = val

    def get_events(self):
        """Logs responses/triggers from keyboard and mouse."""

        events = event.getKeys(timeStamped=self.session.clock)

        # Handle keyboard events
        for key, t in events:
            if key == 'q':
                self.session.close()
                self.session.quit()
                return events  # Exit early if 'q' is pressed

            # Check if the key was already pressed in the previous frame
            if key not in self.session.keys_pressed_last_frame:
                event_type = 'pulse' if key == self.session.mri_trigger else 'key_press'
                self._log_event(event_type, key, t)

                if key != self.session.mri_trigger:
                    self.last_resp = key
                    self.last_resp_onset = t
        clicked_digits = []  # Store clicked digits in this list
        # Update keys_pressed_last_frame for the next iteration
        self.session.keys_pressed_last_frame = events  # Store the current frame's events
        # Handle mouse clicks
        if self.session.virtual_response_box:
            for i, digit in enumerate(self.session.virtual_response_box):  # skip the rectangle (i==0)
                if i == 0:
                    continue
                # show feedback by digit color change
                if self.session.mouse.getVisible():
                    if digit.contains(self.session.mouse):
                        digit.color = "darkgrey"
                    else:
                        digit.color = "white"
                if self.session.mouse.getPressed()[0] and not self.session.mouse_was_pressed:
                    if digit.contains(self.session.mouse):
                        clicked_digits.append(i - 1)  # Store the clicked digit index
                    # Decide on the final response after checking all digits
                    if clicked_digits:
                        # response = self.session.settings["numpad"]["digits"][i - 1]
                        response = self.session.settings["numpad"]["digits"][clicked_digits[0]]
                        t = self.session.clock.getTime()
                        self._log_event(event_type='mouse_click', response=response, t=t)  # Or 'mouse_click'
                        self.last_resp = response
                        self.last_resp_onset = t
                        break
                self.session.mouse.clickReset()  # Update mouse position
            # Track mouse button state
            self.session.mouse_was_pressed = self.session.mouse.getPressed()[0]
        return events

    def load_next_trial(self, phase_dur):
        """ Loads the next trial by calling the session's
        'create_trial' method.

        Parameters
        ----------
        phase_dur : int/float
            Duration of phase
        """
        self.draw()  # draw this phase, then load
        self.session.win.flip()

        load_start = self.session.clock.getTime()
        self.session.create_trial(self.trial_nr+1)  # call create_trial method from session!
        load_dur = self.session.clock.getTime() - load_start

        if self.timing == 'frames':
            load_dur /= self.session.actual_framerate

        if load_dur > phase_dur:  # overshoot! not good!
            logging.warn(f'Time to load stimulus ({load_dur:.5f} {self.timing}) is longer than'
                         f' phase-duration {phase_dur:.5f} (trial {self.trial_nr})!')

    def run(self):
        """ Runs through phases. Should not be subclassed unless
        really necessary. """
        # Because the first flip happens when the experiment starts,
        # we need to compensate for this during the first trial/phase
        if self.session.first_trial:
            # must be first trial/phase
            if self.timing == 'seconds':  # subtract duration of one frame
                self.phase_durations[0] -= 1./self.session.actual_framerate * 1.1  # +10% to be sure
            else:  # if timing == 'frames', subtract one frame 
                self.phase_durations[0] -= 1
            
            self.session.first_trial = False

        for phase_dur in self.phase_durations:  # loop over phase durations
            # pass self.phase *now* instead of while logging the phase info.
            self.session.win.callOnFlip(self.log_phase_info, phase=self.phase)
            #self.log_phase_info(phase=self.phase)

            if self.timing == 'seconds':
                # Loop until timer is at 0!
                self.session.timer.add(phase_dur)
                if self.phase == 2:  # TODO: this should logically sit somewhere else
                    self.buffer_zone = self.session.timer.getTime() + 0.1  # 100 ms buffer zone
                    # print(f"Buffer zone: {self.buffer_zone}")
                while self.session.timer.getTime() < 0 and not self.exit_phase and not self.exit_trial:
                    self.draw()
                    if self.draw_each_frame:
                        self.session.win.flip()
                        self.session.nr_frames += 1
                    self.get_events()
            else:
                # Loop for a predetermined number of frames
                # Note: only works when you're sure you're not 
                # dropping frames
                for _ in range(phase_dur):

                    if self.exit_phase or self.exit_trial:
                        break

                    self.draw()
                    self.session.win.flip()
                    self.get_events()
                    self.session.nr_frames += 1

            if self.exit_phase:  # broke out of phase loop
                self.session.timer.reset()  # reset timer!
                self.exit_phase = False  # reset exit_phase
            if self.exit_trial:
                self.session.timer.reset()
                break

            if not self.phase == max(range(len(self.phase_durations))):  # I do not know why but we need this
                self.phase += 1  # advance phase

    @staticmethod
    def wait(delay_ms):
        """Pauses for the specified delay in milliseconds without blocking."""
        start_time = time.time()
        while (time.time() - start_time) * 1000 < delay_ms:
            pass  # Do nothing, just wait