# -*- coding: utf-8 -*-

import re
import json
import logging
import xml.etree.ElementTree as ET

from preupg.xmlgen.xml_tags import GLOBAL_DIC_VALUES
from preupg.logger import log_message
from preupg.exception import (MissingElementException,
                              AttrNotFoundException,
                              EmptyTextException)


class XmlJsonConverter(object):
    '''
        Converts xml file (result.xml) into more readable
        JSON (result.json) file
        By default converts:
            from <TestResult>:
                end-time(attribute), start-time(attribute)
                inside:
                    target-address(text)
            from <rule-result>:
                inside:
                    result(text), set-value(idref), check-import(text)
    '''
    def __init__(self, file_name, additional_rule_elements=None, verbose=False):
        '''
        Additional_rule_elements -
        additional attributes from <rule-result> element

        verbose - log all warnings like if you want show text from some
        element but text is empty of missing, or attribute etc...
        '''
        self.verbose = verbose
        self.namespace = {}
        self.namespace_key = 'ns0'
        self.result_dict = {"general": {}, "results": {}}
        # dictionary formats:
        # {"result": "text"} -> text
        # {"check": "system"} -> attribute system
        # {"check": ["system","text"]} -> more than one attr/text
        # from the same element
        # <TestResult>
        self.testResult_attibutes = ["end-time", "start-time"]
        self.testResult_elements = {"target-address": "text", "set-value": "text"}

        self.rule_result_elements = {"result": "text", "check-import": "text"}
        if additional_rule_elements is not None:
            self.rule_result_elements.update(additional_rule_elements)

        self.root = self.getRootElement(self.parseXML(file_name))
        self.findNamespace(self.root)

    def convert(self):
        # process <TestResult>
        try:
            self.testResult = self.findTestResult(self.root)
        except MissingElementException as missing_ele_report:
            log_message(missing_ele_report, level=logging.ERROR)
        self.processGeneral()
        # process each <rule-result>
        try:
            self.rule_results = self.findRuleResults(self.testResult)
        except MissingElementException as missing_ele_report:
            log_message(missing_ele_report, level=logging.ERROR)
        self.processResults()
        return self.getJsonText()

    def findNamespace(self, root_element):
        """
        root_element = <Element '{NAMESPACE}status'...>
        """
        parsed_namespace = re.split('\{|\}', str(root_element))
        parsed_namespace = str(parsed_namespace[1])
        self.namespace[self.namespace_key] = "{"+parsed_namespace+"}"

    @staticmethod
    def parseXML(xml):
        return ET.parse(xml)

    @staticmethod
    def getRootElement(xml_object):
        return xml_object.getroot()

    def namespaceWrap(self, path):
        ns_url = self.namespace[self.namespace_key]
        return path.replace(self.namespace_key+":", ns_url)

    def findTestResult(self, root_element):
        """
        Find the <ROOT>...<TestResult> element in xml
        """
        xpath_to_test_result = self.namespaceWrap(".//ns0:TestResult")
        test_result_element = root_element.findall(xpath_to_test_result)
        if not test_result_element:
            raise MissingElementException("Cannot find <TestResult> in xml file")
        return test_result_element[0]

    def findRuleResults(self, testResult):
        """
        Find the <TestResult>...<rule-result> elemnt in xml
        """
        xpath_to_rule_elem = self.namespaceWrap("./ns0:rule-result")
        rule_results = testResult.findall(xpath_to_rule_elem)
        if not rule_results:
            raise MissingElementException("Cannot find <rule-result> in xml file")
        return rule_results

    def findInnerElement(self, outer_element, element):
        """
        Get all elements from outer_element...element
        """
        xpath_elem_in_outer_element = self.namespaceWrap(".//ns0:"+element)
        inner_element = outer_element.findall(xpath_elem_in_outer_element)
        if not inner_element:
            raise MissingElementException(
                "Cannot find specific element {0} inside {1} in xml"
                .format(element,
                        self.removeNamespace(outer_element)))
        return inner_element

    def processGeneral(self):
        """
        Process everything in from <TestResult>
        until first <rule-result>
        """
        for attribute in self.testResult_attibutes:
            try:
                testResult_attribute = self.wrapElementAttrInDict(self.testResult, attribute)
                self.addOptToResultDict(self.result_dict, "general", testResult_attribute)
            except AttrNotFoundException as missing_attr:
                log_message(missing_attr, level=logging.ERROR)

        test_result_dict = self.parseDictOfElements(self.testResult, self.testResult_elements)
        self.addOptToResultDict(self.result_dict, "general", test_result_dict)

    def processResults(self):
        """
        Process every <rule-result> element
        """
        all_results = {}
        for rule in self.rule_results:
            rule_result_dict = {}
            element_idref = self.getDataFromElement(rule, "idref")
            #  possibility to process also <rule-result> attibutes
            rule_result_dict[element_idref] = self.parseDictOfElements(rule, self.rule_result_elements)
            all_results.update(rule_result_dict)

        self.addOptToResultDict(self.result_dict, "results", all_results)

    def parseDictOfElements(self, outer_element, elements_dict):
        """
            Parse text or attributes inside
            outer_element into dictionary
            based on element_dict

        element_dict :
           {result: text} -> text
           {check: system} -> attribute system
           {check: [system,text]} -> more than one attr/text
                                    from the same element
        """
        element_dict = {}
        for element_name, attribute in elements_dict.iteritems():
            try:
                element = self.findInnerElement(outer_element, element_name)
            except MissingElementException as missing_ele_report:
                log_message(missing_ele_report, level=logging.ERROR)

            self.checkFoundElement(element, attribute)
            if element:
                try:
                    element_dict.update(self.parseElementAttributes(element, attribute))
                except EmptyTextException:
                    pass
                except AttrNotFoundException as err_mesg:
                    log_message(err_mesg, level=logging.ERROR)

        return element_dict

    def checkFoundElement(self, element, attribute):
        '''
        Control each element whether it makes sense
        to process them (like text is empty attribute
        doesn't exit etc..)

        '''
        for elem in element:
            # {check: [system,text]}
            if type(attribute) is list:
                for attr in attribute:
                    try:
                        self.checkForValidAttribute(elem, attr)
                    except AttrNotFoundException as err_mesg:
                        attribute.remove(attr)
                        if self.verbose:
                            log_message(err_mesg, level=logging.ERROR)
            # {check: system} -> attribute system
            else:
                try:
                    self.checkForValidAttribute(elem, attribute)
                except AttrNotFoundException as err_mesg:
                    element.remove(elem)
                    if self.verbose:
                        log_message(err_mesg, level=logging.ERROR)

    def checkForValidAttribute(self, element, attribute):
        '''
        Check if text or attribute is empty or missing
        if so make report about it and don't bother with it anymore
        '''
        if attribute == "text":
            text = self.getDataFromElement(element, attribute)
            if text is None or text.strip() == '':
                raise AttrNotFoundException("Text in \"{0}\" element is empty doesn't exist"
                                   .format(self.removeNamespace(element)))
        else:
            attr = self.getDataFromElement(element, attribute)
            if attr is None:
                raise AttrNotFoundException("Cannot find attribute \"{0}\" in \"{1}\" element"
                                   .format(attribute, self.removeNamespace(element)))

    def parseElementAttributes(self, element, attribute):
        """
            Sort elements into 2 groups:
                multiple same elements:
                    <foo></foo><foo></foo>...
                single element:
                    <foo></foo>
        """
        element_dict = {}
        multiple = True if len(element) > 1 else False
        # { check: ["system", "text"] }
        if type(attribute) is list:
            element_tag = self.removeNamespace(element[0])
            dict_of_list_elements = {element_tag: ""}
            list_of_dictionaries = []
            for attr in attribute:
                list_of_dictionaries.append(self.routeTextOrAttribute(element, attr, multiple))
            dict_of_list_elements[element_tag] = self.mergeDictionaries(list_of_dictionaries)
            element_dict.update(dict_of_list_elements)
        else:  # { check : system }
            element_dict.update(self.routeTextOrAttribute(element, attribute, multiple))

        return element_dict

    @staticmethod
    def mergeDictionaries(dictionaries):
        """
        only when want more than one attibute/text from the same element

        dictionaries = [{"element": {"attr": "value of attr"}},
                    {"element": {"attr2": "value of attr2"}}]
        >>> {"element": {"attr": "value of attr", "attr2": "value of attr2"}}
        """
        attributes_with_data = {}
        for dictionary in dictionaries:
            attributes_dict = dictionary.values()[0]
            if type(attributes_dict) is dict:
                for attribute in dictionary.values():
                    attributes_with_data.update(attribute)
            else:  # only for text attribute
                attributes_with_data.update({"text": attributes_dict})
        return attributes_with_data

    def routeTextOrAttribute(self, element, attribute, multiple):
        """
        Call specific function based on attribute
        text, attr: single or multiple
        """
        if attribute is "text":
            if multiple:
                return self.multipleTextElements(element, attribute)
            else:
                return self.singleTextElement(element, attribute)
        else:
            if multiple:
                return self.multipleArributeElements(element, attribute)
            else:
                return self.singleAttibuteElement(element, attribute)

    def singleTextElement(self, element, attribute):
        """
        Process text from single element
        """
        element = element[0]
        data = self.getDataFromElement(element, attribute)
        element_name = self.removeNamespace(element)
        if element_name == "check-import":
            data = self.parseCheckImportOutput(data)
        return {element_name: data}

    def multipleTextElements(self, element, attribute):
        """
        Process text from multiple elements
        """
        text_data = []
        for ele in element:
            data = self.getDataFromElement(ele, attribute)
            element_name = self.removeNamespace(ele)
            if element_name == "check-import":
                    data = self.parseCheckImportOutput(data)
            if element_name == "set-value":
                data = self.parseSetValue(ele, data)
                if data is None:
                    continue
            text_data.append(data)

        return {self.removeNamespace(element[0]): text_data}

    def singleAttibuteElement(self, element, attribute):
        """
        Process attribute from single element
        """
        element = element[0]
        data = self.getDataFromElement(element, attribute)
        return {self.removeNamespace(element): {attribute: data}}

    def multipleArributeElements(self, element, attribute):
        """
        Process attribute from multiple elements
        """
        attribute_data = []
        for ele in element:
            data = self.getDataFromElement(ele, attribute)
            attribute_data.append(data)
        return {self.removeNamespace(element[0]): {attribute: attribute_data}}

    @staticmethod
    def getDataFromElement(element, attribute):
        if attribute is "text":
            return element.text
        else:
            return element.get(attribute)

    def wrapElementAttrInDict(self, element, attr):
        """
        element, attr = "foo", "text"
        >>> "{foo: "text from foo element"}"

        element, attr = "foo", "boo"
        >>> "{foo: "value of attribute boo"}"
        """
        if attr == "text":
            if element.text is None:
                raise AttrNotFoundException("Cannot find text in {0} element"
                                   .format(self.removeNamespace(element)))
            return {self.removeNamespace(element[0]): element.text}
        else:
            if element.get(attr) is None:
                raise AttrNotFoundException("Cannot find {0} attribute in {1} element"
                                   .format(attr, self.removeNamespace(element)))
            return {attr: element.get(attr)}

    def removeNamespace(self, element):
        return element.tag.replace(self.namespace[self.namespace_key], "")

    @staticmethod
    def parseCheckImportOutput(text):
        """
        Divide text from <check-import> element
        according to RISK and LOG statements
        """
        risk = []
        log = []
        paragraphs = text.split('\n')
        for paragraph in paragraphs:
            if "preupg.log" in paragraph:
                log.append(paragraph)
            elif "preupg.risk" in paragraph:
                risk.append(paragraph)
            else:
                pass
        parsed_dict = {'risk': risk, 'log': log}
        if not risk:
            parsed_dict.pop('risk')
        if not log:
            parsed_dict.pop('log')
        if not parsed_dict:
            raise EmptyTextException
        return parsed_dict

    def parseSetValue(self, element, data):
        idref = self.getDataFromElement(element, "idref")
        requested_keys = map(lambda key: "xccdf_preupg_value_"+str(key),
                             GLOBAL_DIC_VALUES.keys())
        if idref in requested_keys:
            return {idref: data}
        else:
            return None

    @staticmethod
    def addOptToResultDict(dictionary, where_in_dict, option_dict):
        if(where_in_dict == "general" or where_in_dict == "results"):
            dictionary[where_in_dict].update(option_dict)

    @staticmethod
    def createJson(dictionary):
        return json.dumps(dictionary, indent=4, separators=(',', ': '))

    def getJsonText(self):
        return self.createJson(self.result_dict)
