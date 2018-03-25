package de.psychose2018;

import ipcapture.IPCapture;
import netP5.NetAddress;
import oscP5.OscMessage;
import oscP5.OscP5;
import processing.core.PApplet;
import processing.core.PFont;
import processing.core.PImage;
import themidibus.MidiBus;

import java.util.ArrayList;
import java.util.List;
import java.util.Random;


public class Displayer extends PApplet {

    private final List<ActorData> actorDatas = new ArrayList<>();
    private final List<ActorDisplay> actorDisplays = new ArrayList<>();
    private DatastreamDisplay datastreamDisplay;
    private Simulator simulator;
    private PFont titleFont;
    private PFont mainFont;
    private PFont airflowFont;

    private PImage heart1;
    private PImage heart2;
    private MidiBus midi;
    private IPCapture cam1;
    private IPCapture cam2;
    private OscP5 oscP5;
    private NetAddress netAddressTommy1;
    private NetAddress netAddressTommy2;
    private NetAddress netAddressTommy3;


    private boolean midiDebug = false;

    public void settings() {
        size(1800, 900);
        fullScreen(P3D, 2);
    }

    @Override
    public void setup() {
        frameRate(25);
        
        cam1 = new IPCapture(this, "http://192.168.1.50:/mjpg/video.mjpg", "", "");
        cam1.start();
        cam2 = new IPCapture(this, "http://192.168.1.228:9001/stream.mjpeg", "", "");
        cam2.start();
        oscP5 = new OscP5(this, 12000);
        netAddressTommy1 = new NetAddress("192.168.1.32", 5557);
        netAddressTommy2 = new NetAddress("192.168.1.32", 5558);
        netAddressTommy3 = new NetAddress("192.168.1.32", 5559);

        mainFont = createFont("Droid Sans Mono", 20);
        titleFont = createFont("Droid Sans Mono", 28);
        airflowFont = createFont("Droid Sans Mono", 70);

        heart1 = loadImage("heart1_klein_inv.jpg");
        heart2 = loadImage("heart2_klein_inv.jpg");

        actorDatas.add(new ActorData("merle", "Körper 1"));
        actorDatas.add(new ActorData("uwe", "Körper 2"));
        actorDatas.add(new ActorData("bjoern", "Körper 3"));

        for (ActorData actorData : actorDatas) {
            actorData.setSimulationEnabled(true);
            actorDisplays.add(new ActorDisplay(this, titleFont, mainFont, heart1, heart2, actorData));
        }

        simulator = new Simulator(this, actorDatas);
        datastreamDisplay = new DatastreamDisplay(this);

        midi = new MidiBus(this, 0, 1); // this,input,outputdev
        midi.sendControllerChange(0, 3, 127 / 2);
        midi.sendControllerChange(0, 12, 127 / 2);
        midi.sendControllerChange(0, 14, 127 / 2);
        midi.sendControllerChange(0, 9, 127 / 2);
        midi.sendControllerChange(0, 13, 127 / 2);
        midi.sendControllerChange(0, 15, 127 / 2);

        textFont(mainFont);
    }

    public void draw() {
        background(0);
        fill(255);

        simulator.simulate();

        pushMatrix();
        translate(10, 610);
        datastreamDisplay.display();
        popMatrix();

        // display the actor datas
        for (int i = 0; i < actorDatas.size(); i++) {
            pushMatrix();
            translate(i * 263, 70);
            actorDisplays.get(i).display();
            popMatrix();
        }

        // display airflow of actor 0
        textFont(airflowFont);
        text(actorDatas.get(0).getAirflow(), 905, 90);

        cam1.read();
        cam2.read();
        image(cam1, width - 640, height - 480);
        image(cam2, width - 768, 0);

    }

    private Random randDataStream = new Random();

    void datastreamCallback(ActorData data) {

        int index = 0;

        if("merle".contentEquals(data.getActor())) {
            index = 0;
        }
        if("uwe".contentEquals(data.getActor())) {
            index = 1;
        }
        if("bjoern".contentEquals(data.getActor())) {
            index = 2;
        }


        int foo = randDataStream.nextInt(4);
        switch (foo) {
            case 0:
                datastreamDisplay.addLine(index, "airFlow = " + data.getAirflow());
                break;
            case 1:
                datastreamDisplay.addLine(index, "ekg = " + data.getEkg());
                break;
            case 2:
                datastreamDisplay.addLine(index, "emg = " + data.getEmg());
                break;
            case 3:
                datastreamDisplay.addLine(index, "pulse = " + data.getPulse());
                break;
            case 4:
                datastreamDisplay.addLine(index, "oxygen = " + data.getOxygen());
                break;
        }

    }

    void heartbeatCallback(ActorData data) {

        OscMessage myMessage = new OscMessage("/" + data.getActor() + "/heartbeat");
        myMessage.add(data.isHeartbeat() ? 1 : 0);

        if("merle".contentEquals(data.getActor())) {
            oscP5.send(myMessage, netAddressTommy1);
        } else if("uwe".contentEquals(data.getActor())) {
            oscP5.send(myMessage, netAddressTommy2);
        } else if("bjoern".contentEquals(data.getActor())) {
            oscP5.send(myMessage, netAddressTommy3);
        }

    }

    public void noteOn(int channel, int pitch, int velocity) {
        if (midiDebug) {
            print("Note On:");
            print(" Channel:" + channel);
            print(" Pitch:" + pitch);
            println(" Velocity:" + velocity);
        }
    }

    public void noteOff(int channel, int pitch, int velocity) {
        // set Pads colors
        if (midi != null && pitch >= 40 && pitch <= 51) {
            for (int i = 40; i <= 51; i++) {
                midi.sendNoteOff(9, i, 0);
            }
            midi.sendNoteOn(9, pitch, 10);
        }


    }

    public void controllerChange(int channel, int number, int value) {
        if (midiDebug) {
            print("Controller Change:");
            print(" Channel:" + channel);
            print(" Number:" + number);
            println(" Value:" + value);
        }

        if (channel == 0) {
            float v = (value - 127f / 2f) / (127f / 2f);

            if (number == 3) {
                // temp actor0
                actorDatas.get(0).setTemperatureOffset(ActorData.TEMP_DEFAULT + v * 3f);
            } else if (number == 12) {
                // temp actor1
                actorDatas.get(1).setTemperatureOffset(ActorData.TEMP_DEFAULT + v * 3f);
            } else if (number == 14) {
                // temp actor2
                actorDatas.get(2).setTemperatureOffset(ActorData.TEMP_DEFAULT + v * 3f);
            } else if(number == 9) {
                // pulse actor0
                actorDatas.get(0).setPulseOffset(30 + (int)(ActorData.PULSE_DEFAULT + v * 70f));
            } else if(number == 13) {
                // pulse actor1
                actorDatas.get(1).setPulseOffset(30 + (int)(ActorData.PULSE_DEFAULT + v * 70f));
            } else if(number == 15) {
                // pulse actor2
                actorDatas.get(2).setPulseOffset(30 + (int)(ActorData.PULSE_DEFAULT + v * 70f));
            } else if(number == 16) {
                // airflow actor0
                actorDatas.get(0).setAirflowOffset((int)((value / 127f)  * 1000f));
            }


        }


    }


    public static void main(String... args) {
        PApplet.main("de.psychose2018.Displayer");
    }


}
