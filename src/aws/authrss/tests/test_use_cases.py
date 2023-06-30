from aws.authrss.testing import AWS_AUTHRSS_FUNCTIONAL_TESTING
from io import BytesIO
from lxml import etree
from plone.app.testing import setRoles
from plone.app.testing import SITE_OWNER_NAME
from plone.app.testing import SITE_OWNER_PASSWORD
from plone.app.testing import TEST_USER_ID
from plone.app.testing import TEST_USER_NAME
from plone.app.testing import TEST_USER_PASSWORD
from plone.testing.z2 import Browser

import transaction
import unittest


class TestUseCasesFunctionalTest(unittest.TestCase):
    layer = AWS_AUTHRSS_FUNCTIONAL_TESTING

    def anonymous_browser(self):
        """Browser of anonymous"""
        transaction.commit()
        browser = Browser(self.layer["app"])
        browser.handleErrors = False
        return browser

    def _auth_browser(self, login, password):
        """Browser of authenticated user
        :param login: A known user login
        :param password: The password for this user
        """
        browser = self.anonymous_browser()
        browser.addHeader(
            "Authorization",
            "Basic {}:{}".format(
                login,
                password,
            ),
        )

        return browser

    def manager_browser(self):
        """Browser with Manager authentication
        :return: Browser object with manager HTTP basic authentication header
        """
        return self._auth_browser(SITE_OWNER_NAME, SITE_OWNER_PASSWORD)

    def member_browser(self):
        """Browser with Member authentication
        :return: Browser object with member HTTP basic authentication header
        """
        return self._auth_browser(TEST_USER_NAME, TEST_USER_PASSWORD)

    def rss_feed_urls(self, feed):
        """URLs of an RSS feed
        :param feed: an RSS feed as XML string
        :return: sequence of tarrget URLs of the feed
        """
        namespaces = {
            "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
            "dc": "http://purl.org/dc/elements/1.1/",
            "syn": "http://purl.org/rss/1.0/modules/syndication/",
            "rss": "http://purl.org/rss/1.0/",
        }
        feed_file = BytesIO(feed)
        feed_tree = etree.parse(feed_file)
        return feed_tree.xpath(
            "//rss:items//rdf:li/@rdf:resource", namespaces=namespaces
        )

    def setUp(self):
        self.portal = self.layer["portal"]
        self.request = self.layer["request"]
        self.portal_url = self.portal.absolute_url()
        self.portal_workflow = self.portal.portal_workflow
        # Test User is a Manager
        setRoles(self.portal, TEST_USER_ID, ["Member", "Manager"])
        self.setUpContent()

    def tearDown(self):
        del self.portal[self.foo_collection.id]
        del self.portal[self.foo_folder.id]

    def setUpContent(self):
        from plone.base.interfaces.syndication import IFeedSettings

        # enable syndication globally
        mgr_browser = self.manager_browser()
        mgr_browser.open(f"{self.portal_url}/syndication-controlpanel")
        mgr_browser.getControl(name="form.widgets.allowed:list").value = ["selected"]
        mgr_browser.getControl(name="form.widgets.default_enabled:list").value = [
            "selected"
        ]
        mgr_browser.getControl(
            name="form.widgets.show_syndication_button:list"
        ).value = ["selected"]
        submit = mgr_browser.getControl(name="form.buttons.save")
        submit.click()

        # add a folder foo
        mgr_browser = self.manager_browser()
        mgr_browser.open(f"{self.portal_url}/++add++Folder")
        mgr_browser.getControl(name="form.widgets.IDublinCore.title").value = "Foo"
        mgr_browser.getControl(name="form.buttons.save").click()
        mgr_browser.getLink(id="workflow-transition-publish").click()

        self.foo_folder = self.portal.foo
        self.foo_folder_url = self.foo_folder.absolute_url()

        # configure syndication at folder
        mgr_browser = self.manager_browser()
        mgr_browser.open(self.foo_folder_url)
        mgr_browser.getLink("Syndication").click()

        # ordered selection widget needs js and some clicks
        # we set the feed_types programmatically
        feedsettings = IFeedSettings(self.foo_folder)
        feedsettings.feed_types = ("RSS",)
        transaction.commit()

        # add a collection/topic
        mgr_browser.open(f"{self.portal_url}/++add++Collection")
        mgr_browser.getControl(
            name="form.widgets.IDublinCore.title"
        ).value = "Foo Collection"
        mgr_browser.getControl(name="form.buttons.save").click()
        mgr_browser.getLink(id="workflow-transition-publish").click()

        self.foo_collection = self.portal["foo-collection"]
        self.foo_collection_url = self.foo_collection.absolute_url()

        # We set this topic's criteria such both above created documents appear in it.
        # Note that I do this with the API and not with the browser (too noisy)
        self.foo_collection.setQuery(
            [
                {
                    "i": "portal_type",
                    "o": "plone.app.querystring.operation.string.is",
                    "v": "Document",
                }
            ]
        )
        transaction.commit()

        # configure syndication at collection
        mgr_browser = self.manager_browser()
        mgr_browser.open(self.foo_collection_url)
        mgr_browser.getLink("Syndication").click()

        # ordered selection widget needs js and some clicks
        # we set the feed_types programmatically
        feedsettings = IFeedSettings(self.foo_collection)
        feedsettings.feed_types = ("RSS",)
        transaction.commit()

        # Let's add some content
        # As the foo folder has no content, there's nothing to view in the RSS feeds,
        # either the anonymous one or the private RSS feed for the member.
        mgr_browser.open(f"{self.foo_folder_url}/++add++Document")
        mgr_browser.getControl(name="form.widgets.IDublinCore.title").value = "Title1"
        mgr_browser.getControl(
            name="form.widgets.IDublinCore.description"
        ).value = "Description 1"
        mgr_browser.getControl(name="form.buttons.save").click()
        mgr_browser.getLink(id="workflow-transition-publish").click()
        self.doc1 = self.portal.foo.title1
        self.doc1_url = self.doc1.absolute_url()

        mgr_browser.open(f"{self.foo_folder_url}/++add++Document")
        mgr_browser.getControl(name="form.widgets.IDublinCore.title").value = "Title2"
        mgr_browser.getControl(
            name="form.widgets.IDublinCore.description"
        ).value = "Description 2"
        mgr_browser.getControl(name="form.buttons.save").click()
        mgr_browser.getLink(id="workflow-transition-submit").click()
        self.doc2 = self.portal.foo.title2
        self.doc2_url = self.doc2.absolute_url()

    def test_isSiteSyndicationAllowed(self):
        """Checking global syndication settings"""
        from Products.CMFCore.utils import getToolByName

        syntool = getToolByName(self.portal, "portal_syndication")
        self.assertTrue(syntool.isSiteSyndicationAllowed())

    def test_isProductInstalled(self):
        """Checking our component is installed"""
        from plone.base.utils import get_installer

        installer = get_installer(self.portal, self.request)
        self.assertTrue(installer.is_product_installed("aws.authrss"))

    def test_requiredActionsAreAvailable(self):
        """Checking the required actions are available"""
        from Products.CMFCore.utils import getToolByName

        portal_actions = getToolByName(self.portal, "portal_actions")
        self.assertIn("rss_token", portal_actions["user"].keys())
        self.assertIn("rss", portal_actions["document_actions"].keys())

    def test_FolderFoo(self):
        mgr_browser = self.manager_browser()
        mgr_browser.open(self.foo_folder_url)
        self.assertEqual(mgr_browser.url, self.foo_folder_url)
        self.assertEqual(
            self.portal_workflow.getInfoFor(self.foo_folder, "review_state"),
            "published",
        )

    def test_FolderFooFeedSettings(self):
        from plone.base.interfaces.syndication import IFeedSettings

        feedsettings = IFeedSettings(self.foo_folder)
        self.assertTrue(feedsettings.enabled)
        self.assertFalse(feedsettings.render_body)
        self.assertTupleEqual(("RSS",), feedsettings.feed_types)
        self.assertEqual(15, feedsettings.max_items)

    def test_CollectionFoo(self):
        mgr_browser = self.manager_browser()
        mgr_browser.open(self.foo_collection_url)
        self.assertTrue(mgr_browser.title.startswith("Foo Collection"))
        self.assertEqual(
            self.portal_workflow.getInfoFor(self.foo_collection, "review_state"),
            "published",
        )

    def test_CollectionFooFeedSettings(self):
        from plone.base.interfaces.syndication import IFeedSettings

        feedsettings = IFeedSettings(self.foo_collection)
        self.assertTrue(feedsettings.enabled)
        self.assertFalse(feedsettings.render_body)
        self.assertTupleEqual(("RSS",), feedsettings.feed_types)
        self.assertEqual(15, feedsettings.max_items)

    def test_ReviewStatesOfDocuments(self):
        mgr_browser = self.manager_browser()
        mgr_browser.open(self.doc1_url)
        self.assertEqual(mgr_browser.url, self.doc1.absolute_url())
        self.assertEqual(
            self.portal_workflow.getInfoFor(self.doc1, "review_state"),
            "published",
        )

        mgr_browser = self.manager_browser()
        mgr_browser.open(self.doc2_url)
        self.assertEqual(mgr_browser.url, self.doc2.absolute_url())
        self.assertEqual(
            self.portal_workflow.getInfoFor(self.doc2, "review_state"),
            "pending",
        )

    def test_AnonymousCanSeeDocument1(self):
        # The anonymous may see the 'Title1' document
        anon_browser = self.anonymous_browser()
        anon_browser.open(self.doc1_url)
        self.assertTrue(anon_browser.title.startswith("Title1"))

    def test_AnonymousCantSeeDocument2(self):
        from zExceptions.unauthorized import Unauthorized

        # The anonymous can't access the 'Title2' document
        anon_browser = self.anonymous_browser()
        with self.assertRaises(Unauthorized):
            anon_browser.open(self.doc2_url)

    def test_anonymousCanAccessFooFolderAndSeeRSSLink(self):
        anon_browser = self.anonymous_browser()
        anon_browser.open(self.foo_folder_url)

        self.assertTrue(anon_browser.title.startswith("Foo"))

        tree = etree.HTML(anon_browser.contents)
        links = tree.xpath("//li[@id='document-action-rss']/a")
        self.assertEqual(1, len(links))
        anon_rss_url = links[0].attrib["href"]

        self.assertEqual(anon_rss_url, f"{self.portal_url}/foo/RSS")

    def test_authenticatedCanAccessFooFolderAndSeeTokenRSSLink(self):
        # An authenticated user could see the RSS link with his own private token
        member_browser = self.member_browser()
        member_browser.open(self.foo_folder_url)
        tree = etree.HTML(member_browser.contents)
        links = tree.xpath("//li[@id='document-action-rss']/a")
        self.assertEqual(1, len(links))
        member_rss_url = links[0].attrib["href"]

        self.assertTrue(
            member_rss_url.startswith(f"{self.portal_url}/foo/AUTH-RSS?token=")
        )

        # check is token present
        token = member_rss_url.replace(f"{self.portal_url}/foo/AUTH-RSS?token=", "")
        self.assertEqual(len(token), 32)

    def test_main_feature(self):
        """Viewing the RSS feed of the Foo folder
        Okay, we are now testing the main feature of this component and show that when
        viewing a private feed as anonymous, this feed shows also the elements the
        authenticated member is allowed to view
        """
        from zExceptions.unauthorized import Unauthorized

        # TEST the feed of folder
        # get the rss url of the member
        member_browser = self.member_browser()
        member_browser.open(self.foo_folder_url)
        tree = etree.HTML(member_browser.contents)
        links = tree.xpath("//li[@id='document-action-rss']/a")
        member_rss_url = links[0].attrib["href"]

        # open the member rss url as anonymous
        # doc2 should be in the feed
        anon_browser = self.anonymous_browser()
        anon_browser.open(member_rss_url)
        feed = anon_browser.contents
        feed_urls = self.rss_feed_urls(feed)
        self.assertListEqual([self.doc1_url, self.doc2_url], feed_urls)

        # But anonymous cannot view the last URL of the feed
        with self.assertRaises(Unauthorized):
            anon_browser.open(feed_urls[-1])

        # TEST the collection

        # Viewing the Collection
        # We can now view that topic as Member
        member_browser = self.member_browser()
        member_browser.open(self.foo_collection_url)
        self.assertIn("Title1", member_browser.contents)
        self.assertIn("Title2", member_browser.contents)

        # This collection is also viewable by the anonymous user, but he should not see the
        # 'Title2' document that's in "pending" workflow status
        anon_browser = self.anonymous_browser()
        anon_browser.open(self.foo_collection_url)
        self.assertIn("Title1", anon_browser.contents)
        self.assertNotIn("Title2", anon_browser.contents)

        # Checking the collection syndication link

        # For the member
        tree = etree.HTML(member_browser.contents)
        links = tree.xpath("//li[@id='document-action-rss']/a")
        self.assertEqual(len(links), 1)

        member_rss_url = links[0].attrib["href"]
        self.assertTrue(
            member_rss_url.startswith(f"{self.foo_collection_url}/AUTH-RSS?token=")
        )

        # check is token present
        token = member_rss_url.replace(f"{self.foo_collection_url}/AUTH-RSS?token=", "")
        self.assertEqual(len(token), 32)

        # For the anonymous user
        tree = etree.HTML(anon_browser.contents)
        links = tree.xpath("//li[@id='document-action-rss']/a")
        self.assertEqual(len(links), 1)

        anon_rss_url = links[0].attrib["href"]
        self.assertTrue(anon_rss_url.startswith(f"{self.foo_collection_url}/RSS"))

        # Checking the feeds of the Topic

        # The anonymous feed URL
        anon_browser.open(anon_rss_url)
        feed_urls = self.rss_feed_urls(anon_browser.contents)
        self.assertListEqual([self.doc1_url], feed_urls)

        # And the member feed URL but as anonymous
        anon_browser.open(member_rss_url)
        feed_urls = self.rss_feed_urls(anon_browser.contents)
        self.assertListEqual([self.doc1_url, self.doc2_url], feed_urls)

    def test_AnonymousCantResetToken(self):
        # Resetting the personal token
        # Checking the action link to the personal token
        # The anonymous cannot reset his token
        # Anyway, even if the anonymous knows the URL, he cannot go there
        from zExceptions.unauthorized import Unauthorized

        anon_browser = self.anonymous_browser()
        with self.assertRaises(Unauthorized):
            anon_browser.open(f"{self.portal_url}/@@personal-rss-token")

    def test_MemberCanResetToken(self):
        # Resetting the personal token
        # When the member has this link in his personal actions
        member_browser = self.member_browser()
        member_browser.open(self.portal_url)
        link = member_browser.getLink("RSS Token")
        self.assertEqual(link.url, f"{self.portal_url}/@@personal-rss-token")
