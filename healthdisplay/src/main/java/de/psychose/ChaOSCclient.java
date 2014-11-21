package de.psychose;

import com.illposed.osc.OSCListener;
import com.illposed.osc.OSCMessage;
import com.illposed.osc.OSCPortIn;
import com.illposed.osc.OSCPortOut;

import java.io.IOException;
import java.net.InetAddress;
import java.net.NetworkInterface;
import java.net.SocketException;
import java.net.UnknownHostException;
import java.util.Enumeration;

/**
 * @author: lucas
 * @date: 13.04.14 17:03
 */
public class ChaOSCclient {
    private final static int OSC_CLIENT_PORT = 8123;
    private OSCPortIn portIn;
    private OSCPortOut portOut;

    public ChaOSCclient(String host, int port) throws UnknownHostException, SocketException {
        portOut = new OSCPortOut(InetAddress.getByName(host), port);
        try {
            portIn = new OSCPortIn(OSC_CLIENT_PORT);
        } catch (SocketException se) {
            System.out.println("Port " + OSC_CLIENT_PORT + " already in use. Trying " + OSC_CLIENT_PORT + 1);
            portIn = new OSCPortIn(OSC_CLIENT_PORT + 1);
        }
    }

    public void addListener(String address, OSCListener listener) {
        portIn.addListener(address, listener);
    }

    public boolean stopReceiver() {
        portIn.stopListening();
        return changeChaoscSubscription(false);
    }

    public boolean startReceiver() {
        portIn.startListening();
        return changeChaoscSubscription(true);
    }

    public void sendMessage(final String address, Object... args) {
        try {
            OSCMessage subscribeMessage = new OSCMessage(address);

            for(Object param: args) {
                subscribeMessage.addArgument(param);
            }

            portOut.send(subscribeMessage);
        } catch (IOException e) {
            System.out.println("could not send pulse OSC Message");
            e.printStackTrace();
        }

    }

    private boolean changeChaoscSubscription(boolean subscribe) {
        try {
            OSCMessage subscribeMessage = new OSCMessage("/" + (subscribe ? "subscribe" : "unsubscribe"));
            subscribeMessage.addArgument(getLocalAddress().getHostAddress());
            subscribeMessage.addArgument(OSC_CLIENT_PORT);
            subscribeMessage.addArgument("sekret");
            subscribeMessage.addArgument("statusmonitor");

            portOut.send(subscribeMessage);
            return true;
        } catch (IOException e) {
            e.printStackTrace();
        }

        System.out.println("could not change chaosc subscription message");
        return false;
    }

    private InetAddress getLocalAddress() throws SocketException {
        final Enumeration<NetworkInterface> n = NetworkInterface.getNetworkInterfaces();
        while (n.hasMoreElements()) {
            NetworkInterface e = n.nextElement();

            Enumeration<InetAddress> a = e.getInetAddresses();
            for (; a.hasMoreElements(); ) {
                InetAddress addr = a.nextElement();

                if (addr.isSiteLocalAddress()) {
                    System.out.println("found address: " + addr.getHostAddress());
                    return addr;
                }
            }
        }
        throw new SocketException();
    }

}
