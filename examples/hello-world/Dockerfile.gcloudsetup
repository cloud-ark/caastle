FROM lmecld/clis:gcloud

RUN rm -rf /google-cloud-sdk/.install \
 && cd /google-cloud-sdk && find . | grep docs | xargs rm -rf