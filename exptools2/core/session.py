import os

import yaml
import collections
import os.path as op
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from psychopy import core
from psychopy.visual import Window, TextStim
from psychopy.event import waitKeys, Mouse
from psychopy.monitors import Monitor
from psychopy import logging
from psychopy import prefs as psychopy_prefs
from ..stimuli import create_circle_fixation, create_fixation_cross, create_virtual_response_box
from datetime import datetime
import math
import csv


class Session:
    """Base Session class"""

    def __init__(self, output_str, output_dir=None, settings_file=None):
        """Initializes base Session class.

        parameters
        ----------
        output_str : str
            Name (string) for output-files (e.g., 'sub-01_ses-post_run-1')
        output_dir : str
            Path to output-directory. Default: $PWD/logs.
        settings_file : str
            Path to settings file. If None, exptools2's default_settings.yml is used

        attributes
        ----------
        settings : dict
            Dictionary with settings from yaml
        clock : psychopy Clock
            Global clock (reset to 0 at start exp)
        timer : psychopy Clock
            Timer used to time phases
        exp_start : float
            Time at actual start of experiment
        logfile : psychopy Logfile
            Logfile with info about exp (level >= EXP)
        nr_frames : int
            Counter for number of frames for each phase
        win : psychopy Window
            Current window
        default_fix : TextStim
            Default fixation stim (a TextStim with '+')
        actual_framerate : float
            Estimated framerate of monitor
        """
        self.LOGGING_ENCODER = {
            "DEBUG": 10,
            "INFO": 20,
            "WARNING": 30,
            "ERROR": 40,
            "DATA": 25,
            "EXP": 22
        }
        self.output_str = output_str
        self.output_dir = (
            op.join(os.getcwd(), "logs") if output_dir is None else output_dir
        )
        self.settings_file = settings_file

        self.clock = core.Clock()
        self.timer = core.Clock()
        self.exp_start = None
        self.exp_stop = None
        self.global_log = pd.DataFrame(
            columns=[
                "trial_nr",
                "onset",
                "event_type",
                "phase",
                "response",
                "rt"
            ]
        )
        #self.nr_frames = 0  # keeps track of nr of nr of frame flips
        self.first_trial = True
        self.closed = False

        # track the date
        self.start_time = datetime.now()  # starting date time
        self.name = f"{output_str}_{self.start_time.strftime('%B_%d_%Y_%H_%M_%S')}"

        # Initialize
        self.settings = self._load_settings()
        self.monitor = self._create_monitor()
        self.win = self._create_window()
        self.units = self.settings["preferences"]["general"]["units"]
        # get the visual angle by taking distance and size of the monitor and compute the width of it in degrees
        self.width_deg = math.degrees(2 * math.atan((self.monitor.getWidth() / 2) / self.monitor.getDistance()))
        # calculate how many pixels the screen contains per degree
        self.pix_per_deg = self.win.size[0] / self.width_deg
        self.mouse = Mouse(**self.settings["mouse"], win=self.win)
        self.mouse_was_pressed = None  # place holder
        self.keys_pressed_last_frame = list()  # place holder
        self.logfile = self._create_logfile()  # TODO: do I really need this?
        if self.settings["session"]["fixation_type"] == "circle":
            self.default_fix = create_circle_fixation(self.win)
        elif self.settings["session"]["fixation_type"] == "cross":
            self.default_fix = create_fixation_cross(self.win)
        # define whether mouse clicks or button responses are wanted
        self.response_device = self.settings["session"]["response_device"]
        self.mri_trigger = None  # is set below
        if self.response_device == "mouse":
            self.virtual_response_box = create_virtual_response_box(win=self.win,
                                                                    digits=self.settings["numpad"]["digits"],
                                                                    size=self.settings["numpad"]["size"],
                                                                    units=self.units)
        else:
            self.virtual_response_box = None
        self.test = False  # for quitting
        self.t_per_frame = None  # duration of one frame
        self.mouse_data = []

    def _load_settings(self):
        """Loads settings and sets preferences."""
        default_settings_path = op.join(
            op.dirname(op.dirname(__file__)), "data", "default_settings.yml"
        )
        with open(default_settings_path, "r", encoding="utf8") as f_in:
            default_settings = yaml.safe_load(f_in)

        if self.settings_file is None:
            settings = default_settings
            logging.warn("No settings-file given; using default settings file")
        else:
            if not op.isfile(self.settings_file):
                raise IOError(f"Settings-file {self.settings_file} does not exist!")

            with open(self.settings_file, "r", encoding="utf8") as f_in:
                user_settings = yaml.safe_load(f_in)

            # Update (and potentially overwrite) default settings
            _merge_settings(default_settings, user_settings)
            settings = default_settings

        # Write settings to sub dir
        if not op.isdir(self.output_dir):
            os.makedirs(self.output_dir)

        settings_out = op.join(self.output_dir, self.name + "_expsettings.yml")
        with open(settings_out, "w") as f_out:  # write settings to disk
            yaml.dump(settings, f_out, indent=4, default_flow_style=False)

        exp_prefs = settings["preferences"]  # set preferences globally
        for preftype, these_settings in exp_prefs.items():
            for key, value in these_settings.items():
                pref_subclass = getattr(psychopy_prefs, preftype)
                pref_subclass[key] = value
                setattr(psychopy_prefs, preftype, pref_subclass)
        return settings

    def _create_monitor(self):
        """Creates the monitor based on settings and save to disk."""
        monitor = Monitor(**self.settings["monitor"])
        monitor.setSizePix(self.settings["window"]["size"])
        return monitor

    def _create_window(self):
        """Creates a window based on the settings and calculates framerate."""
        win = Window(monitor=self.monitor.name, **self.settings["window"])
        win.flip()
        self.actual_framerate = win.getActualFrameRate()
        if self.actual_framerate is None:
            logging.warn("framerate not measured, substituting 60 by default")
            self.actual_framerate = 60.0
        self.t_per_frame = 1.0 / self.actual_framerate

        logging.warn(
            f"Actual framerate: {self.actual_framerate:.5f} "
            f"(1 frame = {self.t_per_frame:.5f})"
        )
        return win

    def _create_logfile(self):
        """Creates a logfile."""
        log_path = op.join(self.output_dir, self.name + "_log.txt")
        return logging.LogFile(f=log_path, filemode="w", level=self.LOGGING_ENCODER[self.settings["logging"]["level"]])

    def start_experiment(self):
        """Logs the onset of the start of the experiment."""
        self.exp_start = self.clock.getTime()
        self.clock.reset()  # resets global clock
        self.timer.reset()  # phase-timer
        self.win.recordFrameIntervals = False  # TODO: I think I do not need this anyway
        # set audio hardware
        # self.set_audio_hardware(library=self.settings["preferences"]["general"]["audioLib"])

    def start_block(self):
        self.first_trial = True
        self.timer.reset()

    def _set_exp_stop(self):
        """Called on last win.flip(); timestamps end of exp."""
        self.exp_stop = self.clock.getTime()

    def display_text(self, text, keys=None, duration=None, **kwargs):
        """Displays text on the window and waits for a key response.
        The 'keys' and 'duration' arguments are mutually exclusive.

        parameters
        ----------
        text : str
            Text to display
        keys : str or list[str]
            String (or list of strings) of keyname(s) to wait for
        kwargs : key-word args
            Any (set of) parameter(s) passed to TextStim
        """
        #if keys is None and duration is None:
            #raise ValueError("Please set either 'keys' or 'duration'!")

        if keys is not None and duration is not None:
            raise ValueError("Cannot set both 'keys' and 'duration'!")

        stim = TextStim(self.win, text=text, **kwargs)
        stim.draw()
        self.win.flip()

        if keys is not None:
            waitKeys(keyList=keys)

        if duration is not None:
            core.wait(duration)

    def close(self):
        """'Closes' experiment. Should always be called, even when
        experiment is quit manually (saves onsets to file)."""

        if self.closed:  # already closed!
            return None

        # self.win.callOnFlip(self._set_exp_stop)
        self._set_exp_stop()
        self.win.flip()
        self.win.recordFrameIntervals = False

        print(f"\nDuration experiment: {self.exp_stop:.3f}\n")

        if not self.test:
            #self.plot_frame_intervals()
            #self.plot_frame_intervals2()
            # save data
            self.save_data()

        self.win.close()
        self.closed = True

    def plot_frame_intervals2(self):
        # Create figure with frametimes (to check for dropped frames)
        fig, ax = plt.subplots(figsize=(15, 5))
        ax.plot(self.win.frameIntervals)
        ax.axhline(1.0 / self.actual_framerate, c="r")
        ax.axhline(
            1.0 / self.actual_framerate + 1.0 / self.actual_framerate, c="r", ls="--"
        )
        ax.set(
            xlim=(0, len(self.win.frameIntervals) + 1),
            xlabel="Frame nr",
            ylabel="Interval (sec.)",
            ylim=(-0.01, 0.125),
        )
        fig.savefig(op.join(self.output_dir, self.name + f"_frames.pdf"))

    def plot_frame_intervals(self):
        # calculate some values
        intervalsMS = np.array(self.win.frameIntervals) * 1000
        m = round(np.mean(intervalsMS), 2)
        sd = round(np.std(intervalsMS), 2)
        # se=sd/pylab.sqrt(len(intervalsMS)) # for CI of the mean

        distString = (f"Mean = {m}ms, SD = {sd}, 99% CI(frame) = {round(m-2.58*sd, 2)} - {round(m+2.58*sd, 2)}")
        nTotal = len(intervalsMS)
        nDropped = round(sum(intervalsMS > (1.5 * m)), 2)
        droppedString = f"Dropped frames = {nDropped}/{nTotal} = {round(100*nDropped/float(nTotal), 2)}%"
        # droppedString = msg % (nDropped, nTotal, 100 * nDropped / float(nTotal))

        # plot the frameintervals
        plt.figure(figsize=[12, 8])
        plt.subplot(1, 2, 1)
        plt.plot(intervalsMS, '-')
        plt.ylabel('t (ms)')
        plt.xlabel('frame N')
        plt.title(droppedString)

        plt.subplot(1, 2, 2)
        plt.hist(intervalsMS, 50, histtype='stepfilled')
        plt.xlabel('t (ms)')
        plt.ylabel('n frames')
        plt.title(distString)
        plt.savefig(op.join(self.output_dir, self.name + f"_frames_hist.pdf"))

    def quit(self):
        """Quits Python tread (and window if necessary)."""

        if not self.closed:
            self.close()

        core.quit()

    def save_data(self):
        self._set_exp_stop()
        if not op.isdir(self.output_dir):
            os.makedirs(self.output_dir)

        self.local_log = pd.DataFrame(self.global_log).set_index("trial_nr")
        self.local_log["onset_abs"] = self.local_log["onset"] + self.exp_start

        # Only non-responses have a duration
        nonresp_idx = ~self.local_log.event_type.isin(["mouse_click", "key_press", "trigger", "pulse"])
        last_phase_onset = self.local_log.loc[nonresp_idx, "onset"].iloc[-1]
        dur_last_phase = self.exp_stop - last_phase_onset
        durations = np.append(
            self.local_log.loc[nonresp_idx, "onset"].diff().values[1:], dur_last_phase
        )
        self.local_log.loc[nonresp_idx, "duration"] = durations

        # Same for nr frames
        #nr_frames = np.append(
            #self.local_log.loc[nonresp_idx, "nr_frames"].values[1:], self.nr_frames)
        # Identify and handle NaN values
        # nan_indices = np.isnan(nr_frames)
        # nr_frames[nan_indices] = 0  # Replace NaNs with 0
        #self.local_log.loc[nonresp_idx, "nr_frames"] = nr_frames.astype(int)
        # Round for readability and save to disk
        self.local_log = self.local_log.round(
            {"onset": 3, "onset_abs": 3, "duration": 3}
        )
        f_out = op.join(self.output_dir, self.name + "_events.csv")
        self.local_log.to_csv(f_out, index=True)
        f_out_mouse = op.join(self.output_dir, self.name + "_mouse_data.csv")
        with open(f_out_mouse, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["trial_nr", "x", "y", "time"])  # Write header row
            writer.writerows(self.mouse_data)
        # set saving output to None for RAM
        del self.local_log

    @staticmethod
    def set_audio_hardware(library, latency):
        from psychopy import prefs
        prefs.hardware["audioLib"] = [library]
        prefs.hardware["audioLatencyMode"] = str(latency)
        logging.info(f"Audio hardware is: {prefs.hardware}")


def _merge_settings(default, user):
    """Recursive dict merge. Inspired by dict.update(), instead of
    updating only top-level keys, dict_merge recurses down into dicts nested
    to an arbitrary depth, updating keys. The merge_dct is merged into
    Adapted from https://gist.github.com/angstwad/bf22d1822c38a92ec0a9.

    Parameters
    ----------
    default : dict
        To-be-updated dict
    user : dict
        Dict to merge in default

    Returns
    -------
    None
    """
    for k, v in user.items():
        if (
            k in default
            and isinstance(default[k], dict)
            and isinstance(user[k], collections.abc.Mapping)
        ):
            _merge_settings(default[k], user[k])
        else:
            default[k] = user[k]
