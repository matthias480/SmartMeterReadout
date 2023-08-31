# SmartMeterReadout

This is an example project offering a Python script which can be used to readout the Smart Meter KAIFA MA309M.  
The script is ready to be used for reading the current Smart Meter KAIFA MA309M(H) from vorarlberg netz.  
You just need to insert your decryption key - received by vorarlberg netz (https://webportal.vorarlbergnetz.at) -
in the configuration section (see [line 36](readout-smart-meter.py#L36)) and process the data according to your needs. Here it is printed to console ([line 208](readout-smart-meter.py#L208)).

For other grid operators some adaptations probably need to be made -
e.g. with regard to the frame length (see [line 31](readout-smart-meter.py#L31)) as the length depends on the provided meter information.

## Successfully tested with

* **KAIFA MA309M(H)** provided by [Vorarlberger Energienetze GmbH](https://www.vorarlbergnetz.at/)


## Hardware requirements

* Raspberry Pi (e.g.)
* USB-to-MBUS slave module
  * E.g.:
  * https://www.amazon.de/ZTSHBK-USB-zu-MBUS-Slave-Modul-Master-Slave-Kommunikation-Debugging-Busüberwachung/dp/B09F5FGYVS/
  * https://www.amazon.de/Tedbear-USB-M-Bus-Master-Slave-Kommunikation-Debuggen-Bus%C3%BCberwachung-As-Show/dp/B0827DSGTD/
  * ...
* RJ11/RJ12 cable
  * As only the two middle pins are required, it can be either an RJ11 or an RJ12 cable.
  * Cut off one plug and connect the cable end to the USB-to-MBUS module.

### Pin assignment

```
┌───┬─┬─┬─┬─┬─┬─┬───┐         Pin #    Assignment
│   │1│2│3│4│5│6│   │        ------- ---------------
│   │ │ │ │ │ │ │   │             1   not in use
│   └─┴─┴─┴─┴─┴─┘   │             2   not in use
│                   │             3   MBUS1 (+)
│     RJ12 Jack     │             4   MBUS2 (-)
│                   │             5   not in use
└─────┬───────┬─────┘             6   not in use
      └───────┘            



            ┌──────┬───────────────┐
            │______│               │
NC        6 │______│               │                         ┌───────────────────────────────────┐
NC        5 │______│               │                         │ ┌───┐                             ├───────┐
MBUS2 (-) 4 │______┼───────────────┼───────── - - - ─────────┼─┼─□ │                             │       │
MBUS1 (+) 3 │______┼───────────────┼───────── - - - ─────────┼─┼─□ │                             │       │
NC        2 │______│               │                         │ └───┘                             ├───────┘
NC        1 │______│               │                         └───────────────────────────────────┘
            │      │               │
            └──────┴───────────────┘
```


## Installation

### Requirements

Install the required packages:

```
pip3 install -r requirements.txt
```


## Execution

### Run in foreground (for testing)

```
python3 readout-smart-meter.py
```

### Run as a service (Linux)

```
sudo ln -s /path/to/readout-smart-meter.service /etc/systemd/system/readout-smart-meter.service
sudo systemctl daemon-reload
sudo systemctl start readout-smart-meter.service
```

### Example print output

```
Timestamp:         2023-08-31 12:00:25
VoltageL1:         234.5 V
VoltageL2:         234.7 V
VoltageL3:         235.3 V
CurrentL1:         13.17 A
CurrentL2:         11.08 A
CurrentL3:         13.25 A
RealPower:         -8615 W
RealPowerIn:       0 W
RealPowerOut:      8615 W
RealEnergyIn:      166.429 kWh
RealEnergyOut:     1176.026 kWh
ReactiveEnergyIn:  8.284 kvar
ReactiveEnergyOut: 808.028 kvar
```


## Example message from Smart Meter

### In HEX:
```
68fafa6853ff000167db084b464d10200037748201552100001b663a7466d819644faa8945398a4d461f7ee2470ef90ffb16cd32824aa86760be6755be8f7fd3658d468df42ced68e7ad9fc85ea145d9ef74cdd98247afe2d6c47eeb472b410c0c04ac598e76552206fe21ab26f75dead126b9147ef005b738bee40d43abc888f31b8e1f26a480f7afadd7c679e1a5aa33e1f3d28b3a221ecbad02171229a6cd615b1b016388be1feaba46a1d230c53e71a6263af6aa9a20d1e8750eaf1bac549efbc13c2a0f6123ae78d30b607a16e5b3e27387608a16c3a075e6617aa5b4c70335628b61706d2b4c86941eb20a77777e538aec41f23fc39e7c21dc3c4cf1166872726853ff1101674e88d9e1e46768ef1e9e15968bf0024a19446c2b16b7375714bc44a3d31646558974cac44617f9c9cb3d8859a2432f0e1718b22b4b2eb630ee1dc9108c0ecd87fe3caba6b55bf26886f1ee0bde184b90320aab7a2eee30ecd7a7b8569f82d47025e513b0dc24d1c97b252225ba6f16
```

### Decrypted XML:

<details>
<summary>View XML</summary>
  
```xml
<DataNotification>
  <LongInvokeIdAndPriority Value="00001C4E" />
  <!--08/21/23 23:23:00-->
  <DateTime Value="07E708150117170000FF8880" />
  <NotificationBody>
    <DataValue>
      <Structure Qty="10" >
        <!--0.0.1.0.0.255-->
        <OctetString Value="0000010000FF" />
        <!--08/21/23 23:23:00-->
        <OctetString Value="07E708150117170000FF8880" />
        <Structure Qty="02" >
          <!--0.0.96.1.0.255-->
          <OctetString Value="0000600100FF" />
          <!--bytearray(b'1KFM0200014196')-->
          <OctetString Value="314B464D30323030303134313936" />
        </Structure>
        <Structure Qty="02" >
          <!--0.0.42.0.0.255-->
          <OctetString Value="00002A0000FF" />
          <!--bytearray(b'KFM1200200014196')-->
          <OctetString Value="4B464D31323030323030303134313936" />
        </Structure>
        <Structure Qty="03" >
          <!--1.0.32.7.0.255-->
          <OctetString Value="0100200700FF" />
          <UInt16 Value="0919" />
          <Structure Qty="02" >
            <Int8 Value="FF" />
            <Enum Value="23" />
          </Structure>
        </Structure>
        <Structure Qty="03" >
          <!--1.0.52.7.0.255-->
          <OctetString Value="0100340700FF" />
          <UInt16 Value="090F" />
          <Structure Qty="02" >
            <Int8 Value="FF" />
            <Enum Value="23" />
          </Structure>
        </Structure>
        <Structure Qty="03" >
          <!--1.0.72.7.0.255-->
          <OctetString Value="0100480700FF" />
          <UInt16 Value="0910" />
          <Structure Qty="02" >
            <Int8 Value="FF" />
            <Enum Value="23" />
          </Structure>
        </Structure>
        <Structure Qty="03" >
          <!--1.0.31.7.0.255-->
          <OctetString Value="01001F0700FF" />
          <UInt16 Value="00B0" />
          <Structure Qty="02" >
            <Int8 Value="FE" />
            <Enum Value="21" />
          </Structure>
        </Structure>
        <Structure Qty="03" >
          <!--1.0.51.7.0.255-->
          <OctetString Value="0100330700FF" />
          <UInt16 Value="00D3" />
          <Structure Qty="02" >
            <Int8 Value="FE" />
            <Enum Value="21" />
          </Structure>
        </Structure>
        <Structure Qty="03" >
          <!--1.0.71.7.0.255-->
          <OctetString Value="0100470700FF" />
          <UInt16 Value="00AD" />
          <Structure Qty="02" >
            <Int8 Value="FE" />
            <Enum Value="21" />
          </Structure>
        </Structure>
        <Structure Qty="03" >
          <!--1.0.1.7.0.255-->
          <OctetString Value="0100010700FF" />
          <UInt32 Value="00000029" />
          <Structure Qty="02" >
            <Int8 Value="00" />
            <Enum Value="1B" />
          </Structure>
        </Structure>
        <Structure Qty="03" >
          <!--1.0.2.7.0.255-->
          <OctetString Value="0100020700FF" />
          <UInt32 Value="00000000" />
          <Structure Qty="02" >
            <Int8 Value="00" />
            <Enum Value="1B" />
          </Structure>
        </Structure>
        <Structure Qty="03" >
          <!--1.0.1.8.0.255-->
          <OctetString Value="0100010800FF" />
          <UInt32 Value="00012D4A" />
          <Structure Qty="02" >
            <Int8 Value="00" />
            <Enum Value="1E" />
          </Structure>
        </Structure>
        <Structure Qty="03" >
          <!--1.0.2.8.0.255-->
          <OctetString Value="0100020800FF" />
          <UInt32 Value="000D3EB9" />
          <Structure Qty="02" >
            <Int8 Value="00" />
            <Enum Value="1E" />
          </Structure>
        </Structure>
        <Structure Qty="03" >
          <!--1.0.3.8.0.255-->
          <OctetString Value="0100030800FF" />
          <UInt32 Value="0000000A" />
          <Structure Qty="02" >
            <Int8 Value="00" />
            <Enum Value="20" />
          </Structure>
        </Structure>
        <Structure Qty="03" >
          <!--1.0.4.8.0.255-->
          <OctetString Value="0100040800FF" />
          <UInt32 Value="00087F7B" />
          <Structure Qty="02" >
            <Int8 Value="00" />
            <Enum Value="20" />
          </Structure>
        </Structure>
      </Structure>
    </DataValue>
  </NotificationBody>
</DataNotification>
```

</details>

### Datetime Explanation

```
07 E7            <-- Full year, 0x07E7 = 2023
06               <-- Month, June
12               <-- Day of month, 0x12 = 18
02               <-- Day of week, Tuesday
14               <-- Hour of day, 0x14 = 20
2F               <-- Minute of hour, 0x2F = 47
32               <-- Second of minute, 0x32 = 50
FF               <-- Hundredths of second, 0xFF = not specified
80 00            <-- Deviation (offset from UTC), 0x8000 = not specified
80               <-- Clock status, 0x80 = 0b10000000, MSB 1 = summer time
```


## Message / Protocol explanations

With regard to the structure of the M-Bus frames, there is helpful information here:

* https://blog.roysolberg.com/2019/07/smart-meter-1
* https://stadtwerkeschwaz.at/pdfs/Technische%20Beschreibung%20Kundenschnittstelle%20SWS%20Smart%20Meter.pdf
* https://www.salzburgnetz.at/content/dam/salzburgnetz/dokumente/stromnetz/Technische-Beschreibung-Kundenschnittstelle.pdf

Also useful: https://www.photovoltaikforum.com/thread/157476-stromz%C3%A4hler-kaifa-ma309-welches-mbus-usb-kabel/?postID=2582715#post2582715


## More links / information

* https://fhburgenland.contentdm.oclc.org/digital/api/collection/p15425dc/id/109982/download
* https://oesterreichsenergie.at/fileadmin/user_upload/Smart_Meter-Plattform/20200201_Konzept_Kundenschnittstelle_SM.pdf
* https://www.gurux.fi/
* https://www.gurux.fi/GuruxDLMSTranslator


## Smart-Meter Adapter for Austria

"Österreichs E-Wirtschaft", the association of Austrian network operators, commissioned the company
Ginzinger electronic systems GmbH to develop an adapter that should work with all smart meter models
available on the market and make the data easily available in the home network.  
However, it is not clear when this will be available.

* https://www.ginzinger.com/de/wissen-events/techtalk/ginzinger-entwickelt-smart-meter-schnittstelle/
* https://www.ginzinger.com/de/wissen-events/techtalk/ginzinger-zubau-news-1/
* https://oesterreichsenergie.at/aktuelles/neuigkeiten/detailseite/die-smart-booster
* https://oesterreichsenergie.at/smart-meter/technische-leitfaeden


## Credits

Thanks to @greenMikeEU, @micronano0 and @tirolerstefan and all the others for their preceding work.


## Some similar projects

* https://github.com/greenMikeEU/SmartMeterEVNKaifaMA309
* https://github.com/micronano0/RaspberryPi-Kaifa-SmartMeter-Reader
* https://github.com/tirolerstefan/kaifa
* https://github.com/culvermelanie/SmartMeter


## License

This project is licensed under GNU GPLv3+.
