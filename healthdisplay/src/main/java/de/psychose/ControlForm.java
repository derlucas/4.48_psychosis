package de.psychose;

import com.illposed.osc.OSCMessage;
import com.illposed.osc.OSCPortOut;

import javax.swing.*;
import java.io.IOException;
import java.net.SocketException;
import java.net.UnknownHostException;
import java.util.Random;

/**
 * @author: lucas
 * @date: 15.11.14 22:23
 */
public class ControlForm extends JFrame {

    private final int OXY_WOBBLE_WIDTH = 4;
    private final int EMG_WOBBLE_WIDTH = 120;
    private final int EKG_WOBBLE_WIDTH = 90;
    private final float TEMP_WOBBLE_WIDTH = 0.1f;
    private final int AIR_WOBBLE_WIDTH = 50;
    private final int PULSE_WOBBLE_WIDTH = 10;

    private final UpdateInterface updateInterface;
    private final ActorData[] actorDatas;
    private final OSCPortOut tommyOutPort;

    private ActorControl actorControl1;
    private ActorControl actorControl2;
    private ActorControl actorControl3;
    private JPanel rootPanel;

    public ControlForm(UpdateInterface updateInterface) throws SocketException, UnknownHostException {
        super("HD Control");
        this.updateInterface = updateInterface;
        tommyOutPort = new OSCPortOut();

        actorDatas = new ActorData[3];
        actorDatas[0] = new ActorData("merle", "Körper 1");
        actorDatas[1] = new ActorData("uwe", "Körper 2");
        actorDatas[2] = new ActorData("bjoern", "Körper 3");

        setContentPane(rootPanel);
        setResizable(false);
        setDefaultCloseOperation(WindowConstants.EXIT_ON_CLOSE);

        pack();
        setVisible(true);

        new Timer(100, actionEvent -> updateInterface.update(actorDatas)).start();

        new Timer(500, actionEvent -> {
            simulate(actorDatas[0]);
            simulate(actorDatas[1]);
            simulate(actorDatas[2]);
        }).start();

        Timer pulseTimer1 = new Timer(1000, actionEvent -> simulatePulse(actorDatas[0]));
        pulseTimer1.start();

        Timer pulseTimer2 = new Timer(1000, actionEvent -> simulatePulse(actorDatas[1]));
        pulseTimer2.start();

        Timer pulseTimer3 = new Timer(1000, actionEvent -> simulatePulse(actorDatas[2]));
        pulseTimer3.start();

        // refresh the delays for the pulse simulation timers in a not that fast manner
        new Timer(10000, actionEvent -> {
            pulseTimer1.setDelay(60000 / Math.max(60, actorDatas[0].getPulse()));
            pulseTimer2.setDelay(60000 / Math.max(60, actorDatas[1].getPulse()));
            pulseTimer3.setDelay(60000 / Math.max(60, actorDatas[2].getPulse()));
        }).start();

    }

//    int oxy = 0; int ekg = 0; int emg = 0; double temp = 0;int air = 0; int pulse = 60;

    private void simulate(ActorData actorData) {
        if (!actorData.isSimulationEnabled()) return;

        Random random = new Random();
        actorData.setOxygen(95 - OXY_WOBBLE_WIDTH / 2 + random.nextInt(OXY_WOBBLE_WIDTH));
        actorData.setEkg(EKG_WOBBLE_WIDTH / 2 + random.nextInt(EKG_WOBBLE_WIDTH));
        actorData.setEmg(EMG_WOBBLE_WIDTH / 2 + random.nextInt(EMG_WOBBLE_WIDTH));
        actorData.setTemperature(actorData.getTemperatureOffset() - (TEMP_WOBBLE_WIDTH / 2 + random.nextDouble() / 2));
        actorData.setAirflow(AIR_WOBBLE_WIDTH / 2 + random.nextInt(AIR_WOBBLE_WIDTH));
        actorData.setPulse(actorData.getPulseOffset() - PULSE_WOBBLE_WIDTH / 2 + random.nextInt(PULSE_WOBBLE_WIDTH));
//        actorData.setOxygen(oxy++ % 1000);
//        actorData.setEkg(ekg++ % 1000);
//        actorData.setEmg(emg++ % 1000);
//        actorData.setTemperature(temp += 0.1);
//        if(temp > 38.0) temp = 37.0;
//        actorData.setPulse(pulse++);
//        if(pulse > 220) pulse = 60;
//        actorData.setAirflow(air++ % 1000);
    }

    private void simulatePulse(ActorData actorData) {
        if (actorData.isSimulationEnabled()) {
            actorData.setHeartbeat(!actorData.isHeartbeat());
            actorData.setTommyHeartbeat(actorData.isHeartbeat());
        }
    }

    void actorControlChanges(ActorControlChangeEvent event) {
        int index;

        switch (event.getActor()) {
            case "merle":
                index = 0;
                break;
            case "uwe":
                index = 1;
                break;
            case "bjoern":
                index = 2;
                break;
            default:
                return;
        }

        actorDatas[index].setPulseOffset(event.getPulse());
        actorDatas[index].setTemperatureOffset(event.getTemperature());
        actorDatas[index].setSimulationEnabled(event.isSimulationEnabled());
    }


    void startBreathSimulation(ActorControl actorControl) {
        if (actorControl == actorControl1) {

        }
    }

    private void sendHeartBeat() {
        try {
            OSCMessage subscribeMessage = new OSCMessage("/tommyheartbeat");    //TODO: correct path?
            tommyOutPort.send(subscribeMessage);
        } catch (IOException e) {
            System.out.println("could not send pulse OSC Message");
            e.printStackTrace();
        }
    }

    private void createUIComponents() {
        this.actorControl1 = new ActorControl(this, "merle");
        this.actorControl2 = new ActorControl(this, "uwe");
        this.actorControl3 = new ActorControl(this, "bjoern");
    }
}
