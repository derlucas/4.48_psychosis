package de.psychose;

import lombok.Data;
import lombok.RequiredArgsConstructor;

@Data
@RequiredArgsConstructor
public class ActorControlChangeEvent {

    private final String actor;
    private boolean simulationEnabled;
    private int airflow;
    private int pulse;
    private double temperature;
    

}
