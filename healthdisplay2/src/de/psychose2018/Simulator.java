package de.psychose2018;

import java.util.List;
import java.util.Random;

public class Simulator {

    private final static int OXY_WOBBLE_WIDTH = 4;
    private final static int EMG_WOBBLE_WIDTH = 120;
    private final static int EKG_WOBBLE_WIDTH = 90;
    private final static float TEMP_WOBBLE_WIDTH = 0.1f;
    private final static int AIR_WOBBLE_WIDTH = 50;
    private final static int PULSE_WOBBLE_WIDTH = 10;
    private final static long MILLIS_SIMULATION_WAIT_MIN = 10;

    private final Displayer host;
    private long lastMillisSimulation = 0;
    private long lastPulseSimulation[];
    private int actorCount;
    private final List<ActorData> actorDataList;
    private final Random randomDelay = new Random();

    Simulator(Displayer host, List<ActorData> actorData) {
        this.host = host;
        this.actorDataList = actorData;
        this.actorCount = actorData.size();
        lastPulseSimulation = new long[this.actorCount];
    }

    public void simulate() {
        if(host.millis() - lastMillisSimulation > (MILLIS_SIMULATION_WAIT_MIN + randomDelay.nextInt(100))) {
            actorDataList.forEach(this::simulateNumbers);
            actorDataList.forEach(host::datastreamCallback);

            lastMillisSimulation = host.millis();
        }

        for (int i = 0; i < actorCount; i++) {
            ActorData data = actorDataList.get(i);

            if(data.isSimulationEnabled()) {
                if (host.millis() - lastPulseSimulation[i] > 60000 / Math.max(60, data.getPulse())) {
                    simulatePulse(data);
                    host.heartbeatCallback(data);
                    lastPulseSimulation[i] = host.millis();
                }
            }
        }
    }

    private void simulateNumbers(ActorData actorData) {
        if (!actorData.isSimulationEnabled()) return;
        Random random = new Random();
        actorData.setOxygen(95 - OXY_WOBBLE_WIDTH / 2 + random.nextInt(OXY_WOBBLE_WIDTH));
        actorData.setEkg(EKG_WOBBLE_WIDTH / 2 + random.nextInt(EKG_WOBBLE_WIDTH));
        actorData.setEmg(EMG_WOBBLE_WIDTH / 2 + random.nextInt(EMG_WOBBLE_WIDTH));
        actorData.setTemperature(actorData.getTemperatureOffset() - (TEMP_WOBBLE_WIDTH / 2 + random.nextDouble() / 2));

        if(actorData.getAirflowOffset() < 10) {
            actorData.setAirflow(AIR_WOBBLE_WIDTH / 2 + random.nextInt(AIR_WOBBLE_WIDTH));
        } else {
            actorData.setAirflow(actorData.getAirflowOffset() + AIR_WOBBLE_WIDTH / 10 + random.nextInt(AIR_WOBBLE_WIDTH/10));
        }

        actorData.setPulse(actorData.getPulseOffset() - PULSE_WOBBLE_WIDTH / 2 + random.nextInt(PULSE_WOBBLE_WIDTH));
    }

    private void simulatePulse(ActorData actorData) {
        if (actorData.isSimulationEnabled()) {
            actorData.setHeartbeat(!actorData.isHeartbeat());
            actorData.setTommyHeartbeat(actorData.isHeartbeat());
        }
    }

}
