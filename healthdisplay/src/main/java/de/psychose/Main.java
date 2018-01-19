package de.psychose;

import javax.swing.*;
import java.awt.*;
import java.net.SocketException;
import java.net.UnknownHostException;

/**
 * @author: lucas
 * @date: 25.04.14 00:23
 */
public class Main {

    public static Color backgroundColor = Color.black;

    public static void main(String[] args) throws SocketException, UnknownHostException {
        new Main();
    }

    public Main() throws SocketException, UnknownHostException {

        try {
            UIManager.setLookAndFeel("com.sun.java.swing.plaf.gtk.GTKLookAndFeel");
        } catch (Exception e) {
            e.printStackTrace();
        }

        PresenterForm presenterForm = new PresenterForm();
        ControlForm controlForm = new ControlForm(presenterForm);
    }


}
