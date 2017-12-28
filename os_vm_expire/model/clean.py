# Copyright (c) 2016 IBM
#               2017 IRISA
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from os_vm_expire.common import config
from os_vm_expire.model import models
from os_vm_expire.model import repositories as repo
from oslo_log import log
from oslo_utils import timeutils

# from sqlalchemy import sql as sa_sql

import datetime

# Import and configure logging.
CONF = config.CONF
log.setup(CONF, 'osvmexpire')
LOG = log.getLogger(__name__)


def cleanup_softdeletes(model, threshold_date=None):
    """Remove soft deletions from a table.

    :param model: table class to remove soft deletions
    :param threshold_date: soft deletions older than this date will be removed
    :returns: total number of entries removed from the database
    """
    LOG.debug("Cleaning soft deletes: %s", model.__name__)
    session = repo.get_session()
    query = session.query(model)
    query = query.filter_by(deleted=True)
    if threshold_date:
        query = query.filter(model.deleted_at <= threshold_date)
    delete_count = query.delete()
    LOG.info("Cleaned up %(delete_count)s entries for %(model_name)s",
             {'delete_count': delete_count,
              'model_name': model.__name__})
    return delete_count


def cleanup_all(threshold_date=None):
    """Clean up the main soft deletable resources.

    This function contains an order of calls to
    clean up the soft-deletable resources.
    :param threshold_date: soft deletions older than this date will be removed
    :returns: total number of entries removed from the database
    """
    LOG.debug("Cleaning up soft deletions where deletion date"
              " is older than %s", str(threshold_date))
    total = 0
    total += cleanup_softdeletes(models.VmExpire,
                                 threshold_date=threshold_date)

    LOG.info("Cleaned up %s soft deleted entries", total)
    return total


def clean_command(sql_url, min_num_days, verbose, log_file):
    """Clean command to clean up the database.

    :param sql_url: sql connection string to connect to a database
    :param min_num_days: clean up soft deletions older than this date
    :param verbose: If True, log and print more information
    :param log_file: If set, override the log_file configured
    """
    if verbose:
        # The verbose flag prints out log events to the screen, otherwise
        # the log events will only go to the log file
        CONF.set_override('debug', True)

    if log_file:
        CONF.set_override('log_file', log_file)

    LOG.info("Cleaning up soft deletions in the barbican database")
    log.setup(CONF, 'osvmexpire')

    cleanup_total = 0
    current_time = timeutils.utcnow()
    stop_watch = timeutils.StopWatch()
    stop_watch.start()
    try:
        if sql_url:
            CONF.set_override('sql_connection', sql_url)
        repo.setup_database_engine_and_factory()

        threshold_date = None
        if min_num_days >= 0:
            threshold_date = current_time - datetime.timedelta(
                days=min_num_days)
        else:
            threshold_date = current_time
        cleanup_total += cleanup_all(threshold_date=threshold_date)
        repo.commit()

    except Exception as ex:
        LOG.exception('Failed to clean up soft deletions in database.')
        repo.rollback()
        cleanup_total = 0  # rollback happened, no entries affected
        raise ex
    finally:
        stop_watch.stop()
        elapsed_time = stop_watch.elapsed()
        if verbose:
            CONF.clear_override('debug')

        if log_file:
            CONF.clear_override('log_file')
        repo.clear()

        if sql_url:
            CONF.clear_override('sql_connection')

        log.setup(CONF, 'osvmexpire')  # reset the overrides

        LOG.info("Cleaning of database affected %s entries", cleanup_total)
        LOG.info('DB clean up finished in %s seconds', elapsed_time)
