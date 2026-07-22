"""probe_mismatches.py — Find GUI writable properties that don't exist on the connected board.

Connects to the ODrive/ODESC, then tries to read every property path that the
web GUI would write during Apply.  Any path that raises an exception is a
mismatch — the GUI will fail if it tries to write it.

Run with:   python probe_mismatches.py
Output:     mismatch_results.txt  (in same folder)
"""

import odrive
import sys, os, io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mismatch_results.txt")
_out = open(out_path, "w", encoding="utf-8", errors="replace")

def log(s=""):
    print(s, flush=True)
    _out.write(str(s) + "\n")
    _out.flush()

# EXHAUSTIVE list of every writable property from odrivePropertyTree.js and odriveAxisTree.js
# plus hardcoded paths from configCommandGenerator.js.
GUI_WRITABLE_PATHS = [
    # ── odrivePropertyTree.js (root properties) ──
    "ibus_report_filter_k",
    "task_timers_armed",
    "test_property",

    # ── odrivePropertyTree.js (config.*) ──
    "config.enable_uart_a",
    "config.enable_uart_b",
    "config.enable_uart_c",
    "config.uart_a_baudrate",
    "config.uart_b_baudrate",
    "config.uart_c_baudrate",
    "config.enable_can_a",
    "config.enable_i2c_a",
    "config.usb_cdc_protocol",
    "config.uart0_protocol",
    "config.uart1_protocol",
    "config.uart2_protocol",
    "config.max_regen_current",
    "config.brake_resistance",
    "config.enable_brake_resistor",
    "config.dc_bus_undervoltage_trip_level",
    "config.dc_bus_overvoltage_trip_level",
    "config.enable_dc_bus_overvoltage_ramp",
    "config.dc_bus_overvoltage_ramp_start",
    "config.dc_bus_overvoltage_ramp_end",
    "config.dc_max_positive_current",
    "config.dc_max_negative_current",
    "config.error_gpio_pin",
    "config.gpio3_analog_mapping",
    "config.gpio4_analog_mapping",

    # GPIO modes (from configCommandGenerator.js)
    "config.gpio1_mode",
    "config.gpio2_mode",
    "config.gpio3_mode",
    "config.gpio4_mode",
    "config.gpio5_mode",
    "config.gpio6_mode",
    "config.gpio7_mode",
    "config.gpio8_mode",

    # CAN config (from odrivePropertyTree.js)
    "can.config.baud_rate",

    # ── odriveAxisTree.js (axis0.config.*) ──
    "axis0.config.startup_motor_calibration",
    "axis0.config.startup_encoder_index_search",
    "axis0.config.startup_encoder_offset_calibration",
    "axis0.config.startup_closed_loop_control",
    "axis0.config.startup_sensorless_control",
    "axis0.config.startup_homing",
    "axis0.config.enable_step_dir",
    "axis0.config.step_dir_always_on",
    "axis0.config.step_gpio_pin",
    "axis0.config.dir_gpio_pin",
    "axis0.config.enable_watchdog",
    "axis0.config.watchdog_timeout",
    "axis0.config.enable_sensorless_mode",

    # axis0.config.can.*
    "axis0.config.can.node_id",
    "axis0.config.can.is_extended",
    "axis0.config.can.heartbeat_rate_ms",
    "axis0.config.can.encoder_rate_ms",
    "axis0.config.can.encoder_error_rate_ms",
    "axis0.config.can.controller_error_rate_ms",
    "axis0.config.can.motor_error_rate_ms",
    "axis0.config.can.sensorless_error_rate_ms",

    # axis0.config.calibration_lockin.*
    "axis0.config.calibration_lockin.current",
    "axis0.config.calibration_lockin.ramp_time",
    "axis0.config.calibration_lockin.ramp_distance",
    "axis0.config.calibration_lockin.accel",
    "axis0.config.calibration_lockin.vel",

    # axis0.config.sensorless_ramp.*
    "axis0.config.sensorless_ramp.current",
    "axis0.config.sensorless_ramp.ramp_time",
    "axis0.config.sensorless_ramp.ramp_distance",
    "axis0.config.sensorless_ramp.accel",
    "axis0.config.sensorless_ramp.vel",
    "axis0.config.sensorless_ramp.finish_distance",
    "axis0.config.sensorless_ramp.finish_on_vel",
    "axis0.config.sensorless_ramp.finish_on_distance",

    # axis0.config.general_lockin.*
    "axis0.config.general_lockin.current",
    "axis0.config.general_lockin.ramp_time",
    "axis0.config.general_lockin.ramp_distance",
    "axis0.config.general_lockin.accel",
    "axis0.config.general_lockin.vel",
    "axis0.config.general_lockin.finish_distance",
    "axis0.config.general_lockin.finish_on_vel",
    "axis0.config.general_lockin.finish_on_distance",

    # axis0.config.mechanical_brake.*
    "axis0.config.mechanical_brake.gpio_num",
    "axis0.config.mechanical_brake.is_active_low",

    # ── motor ──
    "axis0.motor.config.pre_calibrated",
    "axis0.motor.config.motor_type",
    "axis0.motor.config.pole_pairs",
    "axis0.motor.config.calibration_current",
    "axis0.motor.config.resistance_calib_max_voltage",
    "axis0.motor.config.phase_inductance",
    "axis0.motor.config.phase_resistance",
    "axis0.motor.config.torque_constant",
    "axis0.motor.config.current_lim",
    "axis0.motor.config.current_lim_margin",
    "axis0.motor.config.torque_lim",
    "axis0.motor.config.inverter_temp_limit_lower",
    "axis0.motor.config.inverter_temp_limit_upper",
    "axis0.motor.config.requested_current_range",
    "axis0.motor.config.current_control_bandwidth",
    "axis0.motor.config.acim_autoflux_enable",
    "axis0.motor.config.acim_autoflux_attack_gain",
    "axis0.motor.config.acim_autoflux_decay_gain",
    "axis0.motor.config.acim_gain_min_flux",
    "axis0.motor.config.acim_autoflux_min_Id",
    "axis0.motor.config.bEMF_FF_enable",
    "axis0.motor.config.direction",

    # motor.fet_thermistor.*
    "axis0.motor.fet_thermistor.config.enabled",
    "axis0.motor.fet_thermistor.config.temp_limit_lower",
    "axis0.motor.fet_thermistor.config.temp_limit_upper",

    # motor.motor_thermistor.*
    "axis0.motor.motor_thermistor.config.enabled",
    "axis0.motor.motor_thermistor.config.gpio_pin",
    "axis0.motor.motor_thermistor.config.temp_limit_lower",
    "axis0.motor.motor_thermistor.config.temp_limit_upper",
    "axis0.motor.motor_thermistor.config.poly_coefficient_0",
    "axis0.motor.motor_thermistor.config.poly_coefficient_1",
    "axis0.motor.motor_thermistor.config.poly_coefficient_2",
    "axis0.motor.motor_thermistor.config.poly_coefficient_3",

    # ── encoder ──
    "axis0.encoder.config.mode",
    "axis0.encoder.config.cpr",
    "axis0.encoder.config.bandwidth",
    "axis0.encoder.config.use_index",
    "axis0.encoder.config.find_idx_on_lockin_only",
    "axis0.encoder.config.abs_spi_cs_gpio_pin",
    "axis0.encoder.config.pre_calibrated",
    "axis0.encoder.config.enable_phase_interpolation",
    "axis0.encoder.config.calib_range",
    "axis0.encoder.config.calib_scan_distance",
    "axis0.encoder.config.calib_scan_omega",
    "axis0.encoder.config.ignore_illegal_hall_state",
    "axis0.encoder.config.sincos_gpio_pin_sin",
    "axis0.encoder.config.sincos_gpio_pin_cos",
    "axis0.encoder.config.hall_polarity",
    "axis0.encoder.config.hall_polarity_calibrated",
    "axis0.encoder.config.direction",
    "axis0.encoder.config.use_index_offset",
    "axis0.encoder.config.index_offset",
    "axis0.encoder.config.phase_offset",
    "axis0.encoder.config.phase_offset_float",

    # ── sensorless_estimator ──
    "axis0.sensorless_estimator.config.observer_gain",
    "axis0.sensorless_estimator.config.pll_bandwidth",
    "axis0.sensorless_estimator.config.pm_flux_linkage",

    # ── controller ──
    "axis0.controller.input_pos",
    "axis0.controller.input_vel",
    "axis0.controller.input_torque",
    "axis0.controller.config.control_mode",
    "axis0.controller.config.input_mode",
    "axis0.controller.config.pos_gain",
    "axis0.controller.config.vel_gain",
    "axis0.controller.config.vel_integrator_gain",
    "axis0.controller.config.vel_limit",
    "axis0.controller.config.vel_limit_tolerance",
    "axis0.controller.config.vel_ramp_rate",
    "axis0.controller.config.torque_ramp_rate",
    "axis0.controller.config.circular_setpoints",
    "axis0.controller.config.circular_setpoint_range",
    "axis0.controller.config.homing_speed",
    "axis0.controller.config.inertia",
    "axis0.controller.config.axis_to_mirror",
    "axis0.controller.config.mirror_ratio",
    "axis0.controller.config.load_encoder_axis",
    "axis0.controller.config.input_filter_bandwidth",
    "axis0.controller.config.enable_overspeed_error",
    "axis0.controller.config.enable_torque_mode_vel_limit",
    "axis0.controller.config.enable_gain_scheduling",
    "axis0.controller.config.gain_scheduling_width",
    "axis0.controller.config.enable_vel_limit",
    "axis0.controller.config.spinout_electrical_power_threshold",
    "axis0.controller.config.spinout_mechanical_power_threshold",

    # controller.config.anticogging.*
    "axis0.controller.config.anticogging.pre_calibrated",
    "axis0.controller.config.anticogging.anticogging_enabled",
    "axis0.controller.config.anticogging.calib_anticogging",
    "axis0.controller.config.anticogging.calib_pos_threshold",
    "axis0.controller.config.anticogging.calib_vel_threshold",

    # controller.autotuning.*
    "axis0.controller.autotuning.frequency",
    "axis0.controller.autotuning.torque_amplitude",

    # ── trap_traj ──
    "axis0.trap_traj.config.vel_limit",
    "axis0.trap_traj.config.accel_limit",
    "axis0.trap_traj.config.decel_limit",

    # ── endstops ──
    "axis0.min_endstop.config.gpio_num",
    "axis0.min_endstop.config.enabled",
    "axis0.min_endstop.config.offset",
    "axis0.min_endstop.config.is_active_high",
    "axis0.min_endstop.config.debounce_ms",
    "axis0.max_endstop.config.gpio_num",
    "axis0.max_endstop.config.enabled",
    "axis0.max_endstop.config.offset",
    "axis0.max_endstop.config.is_active_high",
    "axis0.max_endstop.config.debounce_ms",
]

# ── Connect ───────────────────────────────────────────────────────────
log("=" * 70)
log("GUI <-> Board Mismatch Probe (EXHAUSTIVE)")
log("=" * 70)
log()
log("Connecting to ODrive/ODESC...")
try:
    odrv = odrive.find_any(timeout=10)
except Exception as e:
    log(f"FAILED to connect: {e}")
    _out.close()
    sys.exit(1)

fw = f"{getattr(odrv, 'fw_version_major', '?')}.{getattr(odrv, 'fw_version_minor', '?')}.{getattr(odrv, 'fw_version_revision', '?')}"
log(f"Connected -- firmware v{fw}")
log()

# ── Probe each path ──────────────────────────────────────────────────
ok = []
missing = []

for path in GUI_WRITABLE_PATHS:
    parts = path.split(".")
    obj = odrv
    try:
        for p in parts:
            obj = getattr(obj, p)
        ok.append(path)
    except Exception as e:
        missing.append((path, str(e)))

log(f"Total writable paths checked: {len(GUI_WRITABLE_PATHS)}")
log(f"  OK:      {len(ok)}")
log(f"  MISSING: {len(missing)}")
log()

if missing:
    log("-- MISSING PROPERTIES (will fail on Apply) " + "-" * 27)
    for path, err in missing:
        log(f"  X  odrv0.{path}")
        log(f"     {err}")
    log()

log("-- OK PROPERTIES " + "-" * 53)
for path in ok:
    log(f"  OK odrv0.{path}")

log()
log("=" * 70)
log("Done.")
_out.close()
print(f"\nResults saved to {out_path}")
