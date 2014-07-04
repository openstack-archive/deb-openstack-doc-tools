# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

# Configuration variables used inside Scrapy to enable modules/pipelines
# and to affect the behavior of several parts.
#
# All available configuration variables are documente at
# http://doc.scrapy.org/en/latest/topics/settings.html.

from scrapy import linkextractor

BOT_NAME = 'sitemap'
SPIDER_MODULES = ['generator.spiders']
ITEM_PIPELINES = {
    'generator.pipelines.IgnoreDuplicateUrls': 500,
    'generator.pipelines.ExportSitemap': 100,
}
CONCURRENT_REQUESTS = 32
CONCURRENT_REQUESTS_PER_DOMAIN = 32
CONCURRENT_REQUESTS_PER_IP = 32
LOG_LEVEL = 'INFO'
LOGGING_ENABLED = True
RANDOMIZE_DOWNLOAD_DELAY = False
TELNETCONSOLE_ENABLED = False
linkextractor.IGNORED_EXTENSIONS.remove('pdf')
