import os
from os.path import expanduser
import subprocess

home_dir = expanduser("~")

APP_STORE_PATH = ("{home_dir}/.cld/data/deployments").format(home_dir=home_dir)

from cliff.command import Command

class GCloudSetup(Command):
    "Set up gcloud. Run ./restart-cloudark.sh after cld setup gcloud has finished."

    def _execute_cmd(self, cmd):
        err= ''
        output=''
        try:
            chanl = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE, shell=True).communicate()
            err = chanl[1]
            output = chanl[0]
        except Exception as e:
            print(e)
        return err, output

    def _setup_zone(self):
        zones = ['us-central1-a', 'us-central1-b', 'us-central1-c', 'us-central1-f',
                 'us-west1-a', 'us-west1-b', 'us-west1-c',
                 'us-east1-b', 'us-east1-c', 'us-east1-d',
                 'us-east4-a', 'us-east4-b', 'us-east4-c',
                 'southamerica-east1-a', 'southamerica-east1-b', 'southamerica-east1-c',
                 'europe-west1-b', 'europe-west1-c', 'europe-west1-d',
                 'europe-west3-a', 'europe-west3-b', 'europe-west3-c',
                 'europe-west2-a', 'europe-west2-b', 'europe-west2-c',
                 'asia-southeast1-a', 'asia-southeast1-b'
                 'asia-east1-a', 'asia-east1-b', 'asia-east1-c',
                 'asia-northeast1-a', 'asia-northeast1-b', 'asia-northeast1-c',
                 'asia-south1-a', 'asia-south1-b', 'asia-south1-c',
                 'australia-southeast1-a', 'australia-southeast1-b', 'australia-southeast1-c',
                ]
        for z in zones:
            print(z)

        zone = ''
        while True:
            zone = raw_input("Enter zone:" )
            if zone in zones:
                break
            else:
                print("Incorrect region specified. Please choose one of above.")
        return zone

    def _get_gcp_account(self):
        account = raw_input("Enter email address associated with your GCP account>")
        return account

    def take_action(self, parsed_args):
        json_key_file_path = raw_input("Enter path of service account json key file>")

        cloudark_google_setup_details_path = APP_STORE_PATH + "/gcp-service-account-key.json"
        if not os.path.exists(APP_STORE_PATH):
            mkdir_command = ("mkdir -p {app_store_path}").format(app_store_path=APP_STORE_PATH)
            os.system(mkdir_command)

        if os.path.exists(json_key_file_path):
            fp1 = open(json_key_file_path, "r")
            input_lines = fp1.readlines()
            fp = open(cloudark_google_setup_details_path, "w")
            fp.writelines(input_lines)
            fp.close()
            fp1.close()
        else:
            print("File not found.")
            exit()

        print("Setting up GCP account information.")
        account = self._get_gcp_account()

        print("Setting up zone information.")
        zone = self._setup_zone()

        cloudark_google_setup_details_path = APP_STORE_PATH + "/google-creds-cloudark"
        if not os.path.exists(APP_STORE_PATH):
            mkdir_command = ("mkdir -p {app_store_path}").format(app_store_path=APP_STORE_PATH)
            os.system(mkdir_command)

        fp = open(cloudark_google_setup_details_path, "w")
        fp.write("zone:%s\n" % zone.strip())
        fp.write("account:%s" % account.strip())
        fp.close()

    def take_action_prev(self, parsed_args):

        gcloud_df = "Dockerfile.gcloudsetup"
        df = ("FROM lmecld/clis:gcloud \n"
              "WORKDIR /google-cloud-sdk \n"
              "RUN /google-cloud-sdk/bin/gcloud components install beta \n"
              "RUN /bin/bash -c 'find . | grep docs | xargs rm -rf' "
              )

        fp = open(gcloud_df, "w")
        fp.write(df)
        fp.close()

        build_cmd = ("docker build -t gcloudsetup -f {filename} .").format(filename=gcloud_df)
        err, output = self._execute_cmd(build_cmd)

        run_cmd = ("docker run -d gcloudsetup")
        err, output = self._execute_cmd(run_cmd)

        if err:
            print("Error occurred in setting up Google cloud. %s " % err)
            exit()

        cont_id = ''
        if output:
            cont_id = output.strip()
            cp_cmd = ("docker cp {cont_id}:/google-cloud-sdk .").format(cont_id=cont_id)
            err, output = self._execute_cmd(cp_cmd)

            if err:
                print("Error occurred in setting up Google cloud. Exiting.")
                exit()


        os.system("./google-cloud-sdk/install.sh --quiet")
        os.system("./google-cloud-sdk/bin/gcloud auth login")
        os.system("./google-cloud-sdk/bin/gcloud beta auth application-default login")
        os.system("rm -rf google-cloud-sdk")

        stop_cmd = ("docker stop -f {cont_id}").format(cont_id=cont_id)
        self._execute_cmd(stop_cmd)

        rm_cmd = ("docker rm -f {cont_id}").format(cont_id=cont_id)
        self._execute_cmd(rm_cmd)

        rmi_cmd = ("docker rmi gcloudsetup")
        self._execute_cmd(rmi_cmd)
