package de.psychose;

import java.util.HashSet;
import java.util.Random;
import java.util.Set;

public class Simulator {

    private final int EMG_WOBBLE_WIDTH = 120;
    private final int EKG_WOBBLE_WIDTH = 90;
    private final float TEMP_WOBBLE_WIDTH = 0.5f;
    private final int AIR_WOBBLE_WIDTH = 50;

    private ChaOSCclient chaOSCclient;
    private Set<ActorData> actors = new HashSet<>();

    public Simulator(ChaOSCclient chaOSCclient) {
        this.chaOSCclient = chaOSCclient;
    }

    public void addActor(ActorData actor) {
        if (!actors.contains(actor)) {
            actors.add(actor);
        }
    }

    public void removeActor(ActorData actor) {
        if (actors.contains(actor)) {
            actors.remove(actor);
        }
    }

    public void tick() {

        if (actors.size() == 0) {
            return;
        }

        for (ActorData actor : actors) {
            simulate(actor);
        }
    }

    private void simulate(ActorData actorData) {

        Random random = new Random();

        actorData.setEkg(EKG_WOBBLE_WIDTH / 2 + random.nextInt(EKG_WOBBLE_WIDTH));
        actorData.setEmg(EMG_WOBBLE_WIDTH / 2 + random.nextInt(EMG_WOBBLE_WIDTH));
        actorData.setTemperature(36.8f + (TEMP_WOBBLE_WIDTH / 2 + random.nextFloat() / 2));
        actorData.setAirflow(AIR_WOBBLE_WIDTH / 2 + random.nextInt(AIR_WOBBLE_WIDTH));

        chaOSCclient.sendMessage("/" + actorData.getActor().toLowerCase() + "/ekg", actorData.getEkg());
        chaOSCclient.sendMessage("/" + actorData.getActor().toLowerCase() + "/emg", actorData.getEmg());
        chaOSCclient.sendMessage("/" + actorData.getActor().toLowerCase() + "/temperature", actorData.getTemperature());
        chaOSCclient.sendMessage("/" + actorData.getActor().toLowerCase() + "/airFlow", actorData.getAirflow());
    }
}
