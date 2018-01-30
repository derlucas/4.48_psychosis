package de.psychose2018;

import lombok.Data;
import lombok.RequiredArgsConstructor;

/**
 * @author: lucas
 * @date: 17.11.14 21:07
 */
@Data
@RequiredArgsConstructor
public class ActorData {

    public static final float TEMP_DEFAULT = 37.6f;
    public static final int PULSE_DEFAULT = 100;

    private boolean simulationEnabled;

    private final String actor;
    private final String caption;
    private boolean heartbeat;
    private int pulse = 0;
    private int oxygen = 95;
    private int airflow = 10;
    private int ekg = 12;
    private int emg = 10;
    private double temperature = 0;
    private double temperatureOffset = TEMP_DEFAULT;
    private int pulseOffset = PULSE_DEFAULT;
    private boolean tommyHeartbeat;
    private int airflowOffset;

}
