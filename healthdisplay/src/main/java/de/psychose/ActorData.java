package de.psychose;

import lombok.Data;
import lombok.RequiredArgsConstructor;

/**
 * @author: lucas
 * @date: 17.11.14 21:07
 */
@Data
@RequiredArgsConstructor
public class ActorData {

    private boolean simulationEnabled;

    private final String actor;
    private final String caption;
    private boolean heartbeat;
    private int pulse = 67;
    private int oxygen = 95;
    private int airflow = 10;
    private int ekg = 12;
    private int emg = 10;
    private double temperature = 37.6;
    private double temperatureOffset = 0.0;
    private int pulseOffset = 0;
    private boolean tommyHeartbeat;



}
