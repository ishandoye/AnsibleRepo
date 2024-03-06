from collections import defaultdict
from multiprocessing import cpu_count
from multiprocessing.pool import ThreadPool

from ansible.module_utils.raxfacts.base import BaseRaxFactsCollector
from ansible.module_utils.six import iteritems

MAX_THREADS = min(4, cpu_count())


class EndpointFactsCollector(BaseRaxFactsCollector):

    name = "endpoints"
    timeout = 120

    def __init__(self, *args, **kwargs):
        super(EndpointFactsCollector, self).__init__(*args, **kwargs)
        self.curl_path = self.module.get_bin_path("curl")
        self.wget_path = self.module.get_bin_path("wget")

    def can_access_url(self, url, timeout=3, validate_certs=True):
        if self.curl_path:
            base_cmd = "{0} -m {1} -s --output /dev/null".format(
                self.curl_path, timeout
            )
            if not validate_certs:
                base_cmd = "{0} -k".format(base_cmd)

            cmd = "{0} {1}".format(base_cmd, url)
            rc, _, _ = self.module.run_command(cmd)
            return True if rc == 0 else False

        if self.wget_path:
            valid_rc = [0, 8]
            base_cmd = "{0} -O /dev/null --tries=1 -q --timeout={1}".format(
                self.wget_path, timeout
            )
            if not validate_certs:
                base_cmd = "{0} --no-check-certificate".format(base_cmd)

            cmd = "{0} {1}".format(base_cmd, url)
            rc, _, _ = self.module.run_command(cmd)
            return True if rc in valid_rc else False

        return False

    def get_url_map_facts(self, url_map):
        pool = ThreadPool(processes=MAX_THREADS)
        thread_map = defaultdict(list)
        for key, data in iteritems(url_map):
            urls = data["urls"]
            validate_certs = data.get("validate_certs", True)
            for url in urls:
                thread_map[key].append(
                    pool.apply_async(
                        self.can_access_url,
                        (url,),
                        {"validate_certs": validate_certs},
                    )
                )
        pool.close()
        facts = {}
        for key, threads in iteritems(thread_map):
            try:
                facts[key] = all([t.get() for t in threads])
            except Exception:
                facts[key] = False

        facts["all_ok"] = all([v for _, v in iteritems(facts)])
        return facts

    def check_vmm_endpoints(self):
        region_map = {
            "ORD": "us-east-2",
            "IAD": "us-east-1",
            "DFW": "us-west-2",
            "SYD": "ap-southeast-2",
            "HKG": "ap-southeast-1",
            "LON": "eu-west-2",
            "STO": "eu-north-1",
        }
        region = region_map.get(self.metadata.get("rs_region"))
        if not region:
            return {}

        url_map = {
            "aws_kms": {"urls": ["https://kms.{0}.amazonaws.com".format(region)]},
            "cloudwatch_logs": {
                "urls": ["https://logs.{0}.amazonaws.com".format(region)]
            },
            "message_delivery": {
                "urls": ["https://ec2messages.{0}.amazonaws.com".format(region)]
            },
            "session_manager": {
                "urls": ["https://ssmmessages.{0}.amazonaws.com".format(region)]
            },
            "ssm": {"urls": ["https://ssm.{0}.amazonaws.com".format(region)]},
            "s3": {
                "urls": [
                    "https://s3.{0}.amazonaws.com".format(region),
                    "https://s3-{0}.amazonaws.com".format(region),
                ]
            },
            "ssm_installer": {
                "urls": ["https://amazon-ssm-{0}.s3.amazonaws.com".format(region)]
            },
            "platform_services": {"urls": ["https://add-ons.api.manage.rackspace.com"]},
            "platform_services_scripts": {
                "urls": ["https://add-ons.manage.rackspace.com"]
            },
        }

        facts = self.get_url_map_facts(url_map)
        facts["aws_region"] = region
        return facts

    def check_sophos_endpoints(self):
        url_map = {
            "cert_authorities": {
                "urls": [
                    "http://ocsp.globalsign.com",
                    "http://ocsp2.globalsign.com",
                    "http://crl.globalsign.com",
                    "http://crl.globalsign.net",
                    "http://ocsp.digicert.com",
                    "http://crl3.digicert.com",
                    "http://crl4.digicert.com",
                ],
            },
            "ctr_sophos_com": {
                "urls": [
                    "https://mcs.stn100syd.ctr.sophos.com",
                    "https://mcs.stn100yul.ctr.sophos.com",
                    "https://mcs.stn100hnd.ctr.sophos.com",
                    "https://mcs2.stn100syd.ctr.sophos.com",
                    "https://mcs2.stn100yul.ctr.sophos.com",
                    "https://mcs2.stn100hnd.ctr.sophos.com",
                    "https://mcs.stn100gru.ctr.sophos.com",
                    "https://mcs2.stn100gru.ctr.sophos.com",
                    "https://mcs.stn100bom.ctr.sophos.com",
                    "https://mcs2.stn100bom.ctr.sophos.com",
                ],
                "validate_certs": False,
            },
            "hmr_sophos_com": {
                "urls": [
                    "https://dzr-mcs-amzn-eu-west-1-9af7.upe.p.hmr.sophos.com",
                    "https://dzr-mcs-amzn-us-west-2-fa88.upe.p.hmr.sophos.com",
                ],
                "validate_certs": False,
            },
            "hydra_sophos_com": {
                "urls": [
                    "https://mcs-cloudstation-eu-central-1.prod.hydra.sophos.com",
                    "https://mcs-cloudstation-eu-west-1.prod.hydra.sophos.com",
                    "https://mcs-cloudstation-us-east-2.prod.hydra.sophos.com",
                    "https://mcs-cloudstation-us-west-2.prod.hydra.sophos.com",
                    "https://mcs2-cloudstation-eu-west-1.prod.hydra.sophos.com",
                    "https://mcs2-cloudstation-eu-central-1.prod.hydra.sophos.com",
                    "https://mcs2-cloudstation-us-east-2.prod.hydra.sophos.com",
                    "https://mcs2-cloudstation-us-west-2.prod.hydra.sophos.com",
                ],
                "validate_certs": False,
            },
            "sophos_com": {
                "urls": [
                    "https://cloud-assets.sophos.com",
                    "https://cloud.sophos.com",
                    "https://id.sophos.com",
                    "https://central.sophos.com",
                    "https://downloads.sophos.com",
                    "https://sophos.com",
                    "https://sdu-feedback.sophos.com",
                ],
            },
            "sophosupd_com": {
                "urls": [
                    "https://dci.sophosupd.com",
                    "https://d1.sophosupd.com",
                    "https://d2.sophosupd.com",
                    "https://d3.sophosupd.com",
                    "https://t1.sophosupd.com",
                    "https://sus.sophosupd.com",
                    "https://sdds3.sophosupd.com",
                ],
            },
            "sophosupd_net": {
                "urls": [
                    "https://dci.sophosupd.net",
                    "https://d1.sophosupd.net",
                    "https://d2.sophosupd.net",
                    "https://d3.sophosupd.net",
                    "https://sdds3.sophosupd.net",
                ],
            },
            "sophosxl_net": {
                "urls": [
                    "https://4.sophosxl.net",
                    "https://samples.sophosxl.net",
                ],
            },
        }
        return self.get_url_map_facts(url_map)

    def collect(self):
        facts = {
            "sophos": self.check_sophos_endpoints(),
            "vmm": self.check_vmm_endpoints(),
        }
        return facts
