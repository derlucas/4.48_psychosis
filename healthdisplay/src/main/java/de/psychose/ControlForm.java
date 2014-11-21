package de.psychose;

import javax.swing.*;
import java.util.Observable;
import java.util.Observer;

/**
 * @author: lucas
 * @date: 15.11.14 22:23
 */
public class ControlForm extends JFrame {
    private PulseControl pulse1;
    private PulseControl pulse2;
    private PulseControl pulse3;
    private JPanel rootPanel;
    private ActorDisplay actor1;
    private ActorDisplay actor2;
    private ActorDisplay actor3;
    private TemperatureControl temp1;
    private TemperatureControl temp2;
    private TemperatureControl temp3;

    private final ChaOSCclient osCclient;

    public ControlForm(ChaOSCclient chaOSCclient, final ActorData[] actorData) {
        super("HD Control");
        this.osCclient = chaOSCclient;

        setContentPane(rootPanel);
        setResizable(false);
        setDefaultCloseOperation(WindowConstants.EXIT_ON_CLOSE);

        addActor(pulse1, actor1, temp1, actorData[0]);
        addActor(pulse2, actor2, temp2, actorData[1]);
        addActor(pulse3, actor3, temp3, actorData[2]);

        pack();
        setVisible(true);
    }

    private void addActor(final PulseControl pulse, final ActorDisplay display, final TemperatureControl temp, final ActorData actorData) {
        pulse.addObserver(new Observer() {
            @Override
            public void update(Observable o, Object arg) {
                if (arg instanceof PulseData) {
                    final PulseData data = (PulseData) arg;
                    osCclient.sendMessage("/" + actorData.getActor().toLowerCase() + "/heartbeat", data.getHeartbeat(),
                            data.getPulse(), data.getOxygen());

                    // TODO: delete this line, bc tommy will send the real events
                    osCclient.sendMessage("/" + actorData.getActor().toLowerCase() + "/tommyheartbeat");
                }
            }
        });

        temp.addObserver(new Observer() {
            @Override
            public void update(Observable o, Object arg) {
                if (arg instanceof Double) {
                    actorData.setTemperatureOffset((double)arg);
                }
            }
        });

        display.init(actorData, true);
    }

}
