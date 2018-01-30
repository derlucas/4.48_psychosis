package de.psychose2018;

import processing.core.PApplet;
import processing.core.PConstants;
import processing.core.PFont;

import java.util.ArrayList;
import java.util.List;

class DatastreamDisplay {

    private final static int LINES = 23;
    private final PApplet host;
    private PFont mainFont;
    private final List<String> lines1 = new ArrayList<>();
    private final List<String> lines2 = new ArrayList<>();
    private final List<String> lines3 = new ArrayList<>();

    DatastreamDisplay(PApplet host) {
        this.host = host;
        //this.mainFont = host.loadFont("Liberation Mono");
    }

    void display() {

        host.textAlign(PConstants.LEFT);
        host.textSize(20);
        //host.textFont(mainFont);

        int i = 0;

        for(String line: lines1) {
            host.text(line, 0, i++ * 20);
        }

        i = 0;
        for(String line: lines2) {
            host.text(line, 263, i++ * 20);
        }

        i = 0;
        for(String line: lines3) {
            host.text(line, 263 * 2, i++ * 20);
        }

    }


    void addLine(int column, String text) {
        List<String> theList;

        switch (column) {
            default:
            case 0:
                theList = lines1;
                break;
            case 1:
                theList = lines2;
                break;
            case 2:
                theList = lines3;
                break;
        }

        if(theList.size() > LINES) {
            theList.remove(0);
        }

        theList.add(text);
    }
}
