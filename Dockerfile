FROM python:3.9-bullseye
ARG user=1001
ARG home=/home/$user
RUN       pip install requests && \
          pip install arcgis --no-deps && \
          pip install cryptography && \
          pip install requests_ntlm && \
          pip install cachetools && \
          pip install lxml && \
          pip install requests_oauthlib  && \
          pip install requests_toolbelt  && \
          pip install six && \
          pip install ujson && \
          pip install pytz && \
          pip install geomet && \
          pip install Jinja2 && \
          pip install urllib3==1.26.5
RUN addgroup docker &&  useradd -ms /bin/bash -G docker $user
RUN chmod -R 777 $home
WORKDIR $home
USER $user
COPY --chown=$user . .
CMD ["python","chefs_soils.py"]
