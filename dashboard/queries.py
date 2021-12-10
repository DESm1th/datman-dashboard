"""Reusable database queries.
"""
import logging

from sqlalchemy import and_, or_, func

from dashboard import db
from .models import (Timepoint, Session, Scan, Study, Site, Metrictype,
                     MetricValue, Scantype, StudySite, AltStudyCode, User,
                     study_timepoints_table, RedcapConfig)
import datman.scanid as scanid

logger = logging.getLogger(__name__)


def get_studies(name=None, tag=None, site=None, create=False):
    """Find a study or studies based on search terms.

    If no terms are provided all studies in the database will be returned.

    Args:
        name (str, optional): The name of a specific study. If given other
            search terms will be ignored. Defaults to None.
        tag (str, optional): A study tag / code (e.g. SPN01) as found in the
            first part of datman style subject IDs. Defaults to None.
        site (str, optional): A site tag (e.g. CMH) as found in the second
            part of datman style subject IDs. Defaults to None.
        create (bool, optional): Whether to create the study if it doesnt
            exist. This option is ignored if 'name' isn't provided.
            Defaults to False.

    Returns:
        list: A list of matching :obj:`dashboard.models.Study` records. May
            be empty if no matches found.
    """
    query = Study.query

    if not (name or tag or site):
        return query.all()

    if name:
        found = query.filter(Study.id == name).all()
        if create and not found:
            study = Study(name)
            try:
                db.session.add(study)
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                raise e
            found = [study]
        return found

    query = query.filter(Study.id == StudySite.study_id)

    if tag:
        query = query.filter(
            or_(StudySite.code == tag,
                and_(Study.id == AltStudyCode.study_id,
                     StudySite.site_id == AltStudyCode.site_id,
                     AltStudyCode.code == tag))
        )

    if site:
        query = query.filter(
            and_(Study.id == StudySite.study_id,
                 StudySite.site_id == site)
        )

    return query.all()


def find_subjects(search_str):
    """
    Used by the dashboard's search bar
    """
    search_str = search_str.strip().upper()
    query = Timepoint.query.filter(
        func.upper(Timepoint.name).contains(search_str))
    return query.all()


def get_session(name, num):
    """
    Used by datman. Return a specific session or None
    """
    return Session.query.get((name, num))


def get_timepoint(name, bids_ses=None, study=None):
    """
    Used by datman. Return one timepoint or None
    """
    if not bids_ses:
        return Timepoint.query.get(name)

    query = Timepoint.query.filter(Timepoint.bids_name == name)\
                           .filter(Timepoint.bids_session == bids_ses)
    if study:
        query = query.join(
            study_timepoints_table,
            and_((study_timepoints_table.c.timepoint == Timepoint.name),
                 study_timepoints_table.c.study == study))
    return query.first()


def get_study_timepoints(study, site=None, phantoms=False):
    """Obtains all timepoints from Studies model

    Args:
        study: Study codename used in DATMAN
        site: Additionally apply a filter on the timepoints for a specific site
        phantoms: Optional argument to keep phantoms in record

    Returns:
        A list of timepoint names from the specified study. For example:

        ['PACTMD_CMH_ABCD', 'PACTMD_CMH_DEFG', ... ]

        If the site optional arugment is used, then only timepoints
        belonging to site will be returned in a list

    """

    try:
        study = get_studies(study)[0]
    except IndexError:
        logger.error('Study {} does not exist!'.format(study))
        return None

    if site:
        timepoints = [s for s in study.timepoints.all() if s.site.name == site]
    else:
        timepoints = [s for s in study.timepoints.all()]

    if not phantoms:
        timepoints = [s for s in timepoints if not s.is_phantom]

    return [s.name for s in timepoints]


def find_sessions(search_str):
    """
    Used by the dashboard's search bar and so must work around fuzzy user
    input.
    """
    search_str = search_str.strip().upper()
    try:
        ident = scanid.parse(search_str)
    except scanid.ParseException:
        # Not a proper ID, try fuzzy search for name match
        query = Session.query.filter(
            func.upper(Session.name).contains(search_str))
    else:
        if ident.session:
            query = Session.query.filter(
                and_((
                     func.upper(Session.name) ==
                     ident.get_full_subjectid_with_timepoint()),
                     Session.num == ident.session)
            )

            if not query.count():
                ident.session = None

        if not ident.session:
            query = Session.query.filter(
                func.upper(Session.name) ==
                ident.get_full_subjectid_with_timepoint())

    return query.all()


def get_scan(scan_name, timepoint=None, session=None, bids=False):
    """
    Used by datman. Return a list of matching scans or an empty list
    """
    if bids:
        query = Scan.query.filter(Scan.bids_name == scan_name)
    else:
        query = Scan.query.filter(Scan.name == scan_name)

    if timepoint:
        query = query.filter(Scan.timepoint == timepoint)
    if session:
        query = query.filter(Scan.repeat == session)
    return query.all()


def find_scans(search_str):
    """
    Used by the dashboard's search bar and so must work around fuzzy user
    input.
    """
    search_str = search_str.strip().upper()
    try:
        ident, tag, series, _ = scanid.parse_filename(search_str)
    except scanid.ParseException:
        try:
            ident = scanid.parse(search_str)
        except scanid.ParseException:
            # Doesnt match a file name or a subject ID so fuzzy search
            # for...
            # matching scan name
            query = Scan.query.filter(
                func.upper(Scan.name).contains(search_str))
            if query.count() == 0:
                # or matching subid
                query = Scan.query.filter(
                    func.upper(Scan.timepoint).contains(search_str))
            if query.count() == 0:
                # or matching tags
                query = Scan.query.filter(
                    func.upper(Scan.tag).contains(search_str))
            if query.count() == 0:
                # or matching series description
                query = Scan.query.filter(
                    func.upper(Scan.description).contains(search_str))
        else:
            if ident.session:
                query = Scan.query.filter(
                    and_((func.upper(Scan.timepoint) ==
                          ident.get_full_subjectid_with_timepoint()),
                         Scan.repeat == int(ident.session)))
                if not query.count():
                    ident.session = None

            if not ident.session:
                query = Scan.query.filter(
                    func.upper(Scan.timepoint) ==
                    ident.get_full_subjectid_with_timepoint())
    else:
        name = "_".join(
            [ident.get_full_subjectid_with_timepoint_session(), tag, series])
        query = Scan.query.filter(func.upper(Scan.name).contains(name))

    return query.all()


def get_user(username):
    query = User.query.filter(
        func.lower(User._username).contains(func.lower(username)))
    return query.all()


def get_scantypes(tag_id=None, create=False):
    """Get all tags (or one specific tag) defined in the database.

    Args:
        tag_id (str, optional): A single tag to look up. Defaults to None.
        create (bool, optional): Whether to create a new record if tag_id
            doesnt exist. Defaults to False.

    Returns:
        :obj:`list`: A list of Scantype records.
    """
    if not tag_id:
        return Scantype.query.all()

    found = Scantype.query.get(tag_id)
    if found:
        return [found]

    if not create:
        return []

    new_tag = Scantype(tag_id)

    try:
        db.session.add(new_tag)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        raise e

    return [new_tag]


def query_metric_values_byid(**kwargs):
    """Queries the database for metrics matching the specifications.
        Arguments are lists of strings containing identifying names

        Example:
        rows = query_metric_value(Studies=['ANDT','SPINS'],
                                  ScanTypes=['T1'],
                                  MetricTypes=['SNR'])

    """
    # convert the argument keys to lowercase
    kwargs = {k.lower(): v for k, v in kwargs.items()}

    filters = {
        'studies': 'Study.id',
        'sites': 'Site.id',
        'sessions': 'Session.id',
        'scans': 'Scan.id',
        'scantypes': 'ScanType.id',
        'metrictypes': 'MetricType.id'
    }

    arg_keys = set(kwargs.keys())

    bad_keys = arg_keys - set(filters.keys())
    good_keys = arg_keys & set(filters.keys())

    if bad_keys:
        logger.warning(
            'Ignoring invalid filter keys provided:{}'.format(bad_keys))

    q = db.session.query(MetricValue)
    q = q.join(MetricType, MetricValue.metrictype)
    q = q.join(Scan, MetricValue.scan)
    q = q.join(ScanType, Scan.scantype)
    q = q.join(Session_Scan, Scan.sessions)
    q = q.join(Session, Session_Scan.session)
    q = q.join(Site, Session.site)
    q = q.join(Study, Session.study)
    q = q.filter(Scan.bl_comment == None)  # noqa: E711

    for key in good_keys:
        if kwargs[key]:
            q = q.filter(eval(filters[key]).in_(kwargs[key]))
    q = q.order_by(Session.name)
    logger.debug('Query string: {}'.format(str(q)))

    result = q.all()

    return (result)


def query_metric_values_byname(**kwargs):
    """Queries the database for metrics matching the specifications.
        Arguments are lists of strings containing identifying names

        Example:
        rows = query_metric_value(Studies=['ANDT','SPINS'],
                                  ScanTypes=['T1'],
                                  MetricTypes=['SNR'])

    """
    # convert the argument keys to lowercase
    kwargs = {k.lower(): v for k, v in kwargs.items()}

    filters = {
        'studies': 'Study.nickname',
        'sites': 'Site.name',
        'sessions': 'Session.name',
        'scans': 'Scan.name',
        'scantypes': 'ScanType.name',
        'metrictypes': 'MetricType.name',
        'isphantom': 'Session.is_phantom'
    }

    arg_keys = set(kwargs.keys())

    bad_keys = arg_keys - set(filters.keys())
    good_keys = arg_keys & set(filters.keys())

    if bad_keys:
        logger.warning(
            'Ignoring invalid filter keys provided:{}'.format(bad_keys))

    q = db.session.query(MetricValue)
    q = q.join(MetricType, MetricValue.metrictype)
    q = q.join(Scan, MetricValue.scan)
    q = q.join(ScanType, Scan.scantype)
    q = q.join(Session_Scan, Scan.sessions)
    q = q.join(Session, Session_Scan.session)
    q = q.join(Site, Session.site)
    q = q.join(Study, Session.study)
    q = q.filter(Scan.bl_comment == None)  # noqa: E711

    for key in good_keys:
        q = q.filter(eval(filters[key]).in_(kwargs[key]))

    q = q.order_by(Session.name)

    logger.debug('Query string: {}'.format(str(q)))

    result = q.all()

    return (result)


def query_metric_types(**kwargs):
    """Query the database for metric types fitting the specifications"""
    # convert the argument keys to lowercase
    kwargs = {k.lower(): v for k, v in kwargs.items()}

    filters = {
        'studies': 'Study.id',
        'sites': 'Site.id',
        'scantypes': 'ScanType.id',
        'metrictypes': 'MetricType.id'
    }

    arg_keys = set(kwargs.keys())

    bad_keys = arg_keys - set(filters.keys())
    good_keys = arg_keys & set(filters.keys())

    if bad_keys:
        logger.warning(
            'Ignoring invalid filter keys provided: {}'.format(bad_keys))

    q = db.session.query(Study, Site, Scantype, Metrictype) \
          .join(Study.sites) \
          .join(Study.scantypes) \
          .join(Scantype.metrictypes) \
          .distinct()

    for key in good_keys:
        if kwargs[key]:  # Don't add the filter if the option is empty
            q = q.filter(eval(filters[key]).in_(kwargs[key]))

    logger.debug('Query string: {}'.format(str(q)))
    result = q.all()

    return (result)
