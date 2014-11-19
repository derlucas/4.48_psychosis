package de.psychose;

import javax.swing.*;
import java.util.Observable;
import java.util.Observer;

/**
 * @author: lucas
 * @date: 15.11.14 22:23
 */
public class ControlForm {
    private PulseControl pulse1;
    private PulseControl pulse2;
    private PulseControl pulse3;
    private JPanel mainPanel;
    private ActorDisplay actor1;
    private ActorDisplay actor2;
    private ActorDisplay actor3;

    private final ChaOSCclient osCclient;

    public JPanel getMainPanel() {
        return mainPanel;
    }


    public ControlForm(ChaOSCclient chaOSCclient, final ActorData actorData1, final ActorData actorData2, final ActorData actorData3) {
        this.osCclient = chaOSCclient;

        addActor("merle", pulse1, actor1, actorData1);
        addActor("uwe", pulse2, actor2, actorData2);
        addActor("bjoern", pulse3, actor3, actorData3);

        actor1.setShowErrors(true);
        actor2.setShowErrors(true);
        actor3.setShowErrors(true);

    }

    private void addActor(final String actor, PulseControl pulse, ActorDisplay display, ActorData actorData) {
        pulse.addObserver(new Observer() {
            @Override
            public void update(Observable o, Object arg) {
                if(arg instanceof PulseData) {
                    final PulseData data = (PulseData)arg;
                    osCclient.sendPulse(actor, data.getHeartbeat(), data.getPulse(), data.getOxygen());
                }
            }
        });
        display.setCaption(actor);
        display.setActorData(actorData);
    }

}
