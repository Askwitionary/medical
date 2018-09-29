from xml.dom import minidom
from xmljson import badgerfish as bf
from xml.etree.ElementTree import fromstring
from json import dumps, loads
import matplotlib.pyplot as plt
import numpy as np
import re
import datetime


def re_between_first_m(text, tag):
    r = re.search("<{}>(.*)<\/{}>".format(tag, tag), text, flags=re.S)
    if r is None:
        return None
    else:
        return r.group(1)


class Patient:

    def __init__(self, data):
        self.data = data
        self.name = data["name"]["@use"]
        self.given_name = data["name"]["given"]["@V"]
        self.family_name = data["name"]["family"]["@V"]
        self.id = data["identifier"]["id"]["@V"]
        self.authority = data["identifier"]["authority"]["@V"]
        self.primary = data["identifier"]["primary"]["@V"]
        birthyear, birthmonth, birthday = data["birthDateTime"]["@V"].split("-")
        self.birthday = datetime.date(int(birthyear), int(birthmonth), int(birthday))
        self.race = data["raceCode"]["@V"]
        self.gender = data["gender"]["@V"]


class Site:

    def __init__(self, data):

        self.display_name = data["@displayName"]
        self.site = data["@V"]


class HeightWeight:

    def __init__(self, data):

        self.value = data["@V"]
        self.unit = data["@U"]


class Device:

    def __init__(self, data):

        self.vendorID = data["vendorID"]["@V"]
        self.modelID = data["modelID"]["@V"]
        self.serialID = data["serialID"]["@V"]
        self.software_name = data["softwareVersion"]["@name"]
        self.software_version = data["softwareVersion"]["@V"]
        self.name = data["deviceName"]["@V"]
        self.number = data["deviceNumber"]["@V"]


class Cfg:

    def __init__(self, data):

        self.hookupAdvisor = data["hookupAdvisor"]
        self.ackLevel = data["hookupAdvisor"]["ackLevel"]["@V"]
        self.writerSpeed = data["reportConfiguration"]["writerSpeed"]
        self.writerFilter = data["reportConfiguration"]["writerFilter"]
        self.frontalLeadGain = data["reportConfiguration"]["frontalLeadGain"]
        self.chestLeadGain = data["reportConfiguration"]["chestLeadGain"]
        self.reportLeads = data["reportConfiguration"]["reportLeads"]


class Wave_data:

    def __init__(self, data):

        self.lead = data["@lead"]
        self.asizeVT = data["@asizeVT"]
        self.VT = data["@VT"]
        self.label = data["@label"]
        if data["@V"] is None:
            self.data = None
        else:
            self.data = np.array(data["@V"].split(" "))


class Wave:

    def __init__(self, data):

        self.unit = data["@U"]
        self.s = data["@S"]
        self.inv = data["@INV"]
        self.filters = data["filters"]
        self.sampleRate = data["sampleRate"]
        try:
            self.start_time = self.__time_formatter(data["collectTime"]["@gatherBeginTime"])
        except KeyError:
            self.start_time = None
        try:
            self.end_time = self.__time_formatter(data["collectTime"]["@gatherEndTime"])
        except KeyError:
            self.end_time = None
        try:
            self.errorLead = data["errorLead"]["@V"]
        except KeyError:
            self.errorLead = None
        self.data_list = [Wave_data(item) for item in data["ecgWaveform"]]

    @staticmethod
    def __time_formatter(timestring):

        date, time = timestring.split("T")
        year, month, day = date.split("-")
        hour, minute, second = time.split(":")
        return datetime.datetime(int(year), int(month), int(day), int(hour), int(minute), int(second))


class Numbers:

    def __init__(self, data):

        self.ventricularRate = data["ventricularRate"]
        self.atrialRate = data["atrialRate"]
        self.beatCount = data["beatCount"]
        self.signalQuality = data["signalQuality"]["@V"]
        self.PP_Interval = data["PP_Interval"]
        self.RR_Interval = data["RR_Interval"]


class VarGlobal:

    def __init__(self, data):

        measurements = data["global"]
        self.P_Onset = measurements["P_Onset"]
        self.P_Offset = measurements["P_Offset"]
        self.Q_Onset = measurements["Q_Onset"]
        self.Q_Offset = measurements["Q_Offset"]
        self.T_Offset = measurements["T_Offset"]
        self.QRS_Count = measurements["QRS_Count"]
        self.QRS_Duration = measurements["QRS_Duration"]
        self.QT_Interval = measurements["QT_Interval"]
        self.QT_Corrected = measurements["QT_Corrected"]
        self.PR_Interval = measurements["PR_Interval"]
        self.aveRRInterval = measurements["aveRRInterval"]
        self.P_Axis = measurements["P_Axis"]
        self.R_Axis = measurements["R_Axis"]
        self.T_Axis = measurements["T_Axis"]
        self.stJPointOffset = measurements["stJPointOffset"]
        self.P_Duration = measurements["P_Dur"]
        self.RRforQTc = measurements["RRforQTc"]


class Variables:

    # anchor
    def __init__(self, data):

        self.measurements = VarGlobal(data["measurements"])
        self.perLead = data["measurements"]["perLead"]
        self.ecgWaveformMXG = Wave(data["ecgWaveformMXG"])


class Interpretation:

    def __init__(self, data):

        self.statement = data["@V"]
        self.code = data["@code"]
        self.eolFlag = data["@eolFlag"]


class Evt:

    def __init__(self, data):

        self.wavp = data["wavp"]

        self.beat = Beat(data["beat"]["any"])


class Ecg:

    def __init__(self, data):

        self.source = data["@source"]
        self.index = data["@index"]
        self.cfg = Cfg(data["cfg"])
        self.wave = Wave(data["wav"]["ecgWaveformMXG"])
        self.num = Numbers(data["num"])
        self.variables = Variables(data["var"]["medianTemplate"])
        self.interpretation = Interpretation(data["interpretation"]["statement"])
        self.evt = Evt(data["evt"])


class Beat:

    def __init__(self, data):

        self.evtSN = data["@evtSN"]
        self.tpoint_toc = data["tpoint"]["toc"]["@V"]
        self.beat_class = data["class"]


class Examination:

    def __init__(self, data):
        self.fullTestStatus = data["fullTestStatus"]["@V"]
        self.questions = data["questions"]
        self.test_type = data["testInfo"]["testType"]["@V"]
        self.test_subtype = data["testInfo"]["testType"]["@subType"]
        self.hasPacemaker = data["testInfo"]["hasPacemaker"]["@V"]
        self.acquisitionDateTime = data["testInfo"]["acquisitionDateTime"]["@V"]
        self.device = Device(data["device"])
        self.ecg_data = Ecg(data["ecgResting"]["params"]["ecg"])


class Visit:

    def __init__(self, data):
        self.site = Site(data["site"])
        self.initial_height = HeightWeight(data["initialHeight"])
        self.initial_weight = HeightWeight(data["initialWeight"])
        self.order = Examination(data["order"])


class Case:

    def __init__(self, patient_id="G1204428164_0"):
        self.filename = patient_id
        self.__dom = self.__get_minidom_data()
        self.__dic = loads(dumps(bf.data(fromstring(self.__get_str_data_()))))["patientInfo"]

        # todo add more attributes if useful
        # Visit info
        self.visit = Visit(self.__dic["visit"])
        # self.visit_dic = self.__dic["visit"]
        del self.__dic["visit"]
        # Basic info
        self.patient = Patient(self.__dic)

    def __get_minidom_data(self):
        """
        Reads file based on patient_id (or filename)
        :return: minidom object of data
        """

        return minidom.parse("../../data/ecg/{}.xml".format(self.filename))

    def __get_str_data(self):

        with open("../../data/ecg/{}.xml".format(self.filename), 'r', encoding="utf8") as f:
            str_holder = ""
            while 1:
                line = f.readline()
                if line == "":
                    break
                while line[0] == " ":
                    line = line[1:]
                if line == "</dcarRecord>\n":
                    str_holder += line
                elif line == "<dcarRecord>\n":
                    str_holder = line
                else:
                    str_holder += line
        return str_holder

    def __get_str_data_(self):
        with open("../../data/ecg/{}.xml".format(self.filename), 'r', encoding="utf8") as f:
            data = f.read()
        return re_between_first_m(data, "dcarRecord")


if __name__ == "__main__":

    pat = Case()


    n = 100

    wave = pat.visit.order.ecg_data.wave.data_list[0].data

    wave = [float(wave[i]) for i in range(len(wave))][:int(len(wave) / n)]
    freq = 50
    Time = np.linspace(0, int(len(wave) / n) / freq, num=int(len(wave)))

    plt.figure(figsize=(30, 15))
    plt.title('Signal Wave...')
    plt.plot(Time, wave)
    plt.show()