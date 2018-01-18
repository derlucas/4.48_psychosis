package de.psychose;

import javax.swing.*;
import javax.swing.event.ChangeEvent;
import javax.swing.event.ChangeListener;
import java.awt.event.ActionEvent;
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
    private TemperatureControl temp1;
    private TemperatureControl temp2;
    private TemperatureControl temp3;
    private JCheckBox checkBox1;
    private JCheckBox checkBox2;
    private JCheckBox checkBox3;
    private JSlider slider1;

    private final ChaOSCclient osCclient;
    private Timer simulationTimer;
    private Simulator simulator;

    public ControlForm(ChaOSCclient chaOSCclient, final ActorData[] actorData) {
        super("HD Control");
        this.osCclient = chaOSCclient;
        this.simulator = new Simulator(chaOSCclient);

        setContentPane(rootPanel);
        setResizable(false);
        setDefaultCloseOperation(WindowConstants.EXIT_ON_CLOSE);

        addActor(pulse1, temp1, actorData[0]);
        addActor(pulse2, temp2, actorData[1]);
        addActor(pulse3, temp3, actorData[2]);

        pack();
        setVisible(true);

        simulationTimer = new Timer(200, new AbstractAction() {
            @Override
            public void actionPerformed(ActionEvent e) {
                simulator.tick();
            }
        });

        final ChangeListener changeListener = new ChangeListener() {
            @Override
            public void stateChanged(ChangeEvent e) {
                if (checkBox1.isSelected() || checkBox2.isSelected() || checkBox3.isSelected()) {
                    simulationTimer.start();
                }
                else {
                    simulationTimer.stop();
                }

                if (checkBox1.isSelected()) {
                    simulator.addActor(actorData[0]);
                } else {
                    simulator.removeActor(actorData[0]);
                }
                if (checkBox2.isSelected()) {
                    simulator.addActor(actorData[1]);
                } else {
                    simulator.removeActor(actorData[1]);
                }
                if (checkBox3.isSelected()) {
                    simulator.addActor(actorData[2]);
                } else {
                    simulator.removeActor(actorData[2]);
                }
            }
        };
        checkBox1.addChangeListener(changeListener);
        checkBox2.addChangeListener(changeListener);
        checkBox3.addChangeListener(changeListener);

        slider1.addChangeListener(new ChangeListener() {
            @Override
            public void stateChanged(ChangeEvent e) {
                actorData[0].setAirflow(slider1.getValue());
            }
        });
    }

    private void addActor(final PulseControl pulse, final TemperatureControl temp, final ActorData actorData) {
        pulse.addObserver(new Observer() {
            @Override
            public void update(Observable o, Object arg) {
                if (arg instanceof PulseData) {
                    final PulseData data = (PulseData) arg;
                    osCclient.sendMessage("/" + actorData.getActor().toLowerCase() + "/heartbeat",
                                          data.getHeartbeat() ? 1 : 0,
                                          data.getPulse(), data.getOxygen());

                    // TODO: delete this line, bc tommy will send the real events
                    //osCclient.sendMessage("/" + actorData.getActor().toLowerCase() + "/tommyheartbeat");
                }
            }
        });

        temp.addObserver(new Observer() {
            @Override
            public void update(Observable o, Object arg) {
                if (arg instanceof Double) {
                    double dbl = (double)arg;
                    actorData.setTemperatureOffset((float)dbl);
                }
            }
        });
    }
}
