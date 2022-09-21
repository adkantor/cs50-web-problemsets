import json

from django.test import TestCase, Client
from django.urls import reverse, resolve

from .models import User, Post
from . import views
from django.conf import settings

from django.test import LiveServerTestCase
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException


# initialize the APIClient app
client = Client()


class IndexPageViewTestCase(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Create users
        u1 = User.objects.create(username='u1')        
        # create  posts
        for _ in range(25):
            Post.objects.create(created_by=u1)


    def test_view_url_exists_at_proper_location(self):
        """ Tests whether page is properly loaded. """        
        response = client.get("/")
        self.assertEqual(response.status_code, 200)        


    def test_view_url_by_name(self):
        """ Tests whether page is accessible by name. """
        response = client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)


    def test_view_uses_correct_template(self):
        """ Tests whether page uses correct template. """
        response = client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'network/index.html')


    def test_view_contains_correct_html(self):
        response = client.get(reverse('index'))
        self.assertContains(response, '<div class="posts">')


    def test_view_does_not_contain_incorrect_html(self):
        response = client.get(reverse('index'))
        self.assertNotContains(response, 'This should not be on the page.')


    def test_view_url_resolves_homepageview(self):
        view = resolve('/')
        self.assertEqual(
            view.func.__name__,
            views.index.__name__
        )


    def test_view_pagination(self):
        """ Tests page pagination. """
        response = client.get('/')
        
        # Request without argument: make sure 10 posts are returned in the context
        self.assertEqual(len(response.context["page_obj"]), 10)

        # Send get request to index page for page 1 and store response
        response = client.get("/?page=1")
        # Make sure 10 posts are returned in the context
        self.assertEqual(len(response.context["page_obj"]), 10)

        # Send get request to index page for page 2 and store response
        response = client.get("/?page=2")
        # Make sure 10 posts are returned in the context
        self.assertEqual(len(response.context["page_obj"]), 10)

        # Send get request to index page for page 3 and store response
        response = client.get("/?page=3")
        # Make sure 5 posts are returned in the context
        self.assertEqual(len(response.context["page_obj"]), 5)




class FollowingPageViewTestCase(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Create users
        u1 = User.objects.create(username='u1')
        u2 = User.objects.create(username='u2')
        u3 = User.objects.create(username='u3')
        u4 = User.objects.create(username='u4')        

        # create posts
        p1 = Post.objects.create(created_by=u1)
        p2 = Post.objects.create(created_by=u2)
        p3 = Post.objects.create(created_by=u3)
        for _ in range(25):
            Post.objects.create(created_by=u4)

        # create follows
        u1.following.add(u2)
        u2.following.add(u1)
        u1.following.add(u4)


    def setUp(self):
        # log in user 1
        u1 = User.objects.get(pk=1)
        client.force_login(u1)


    def tearDown(self):
        client.logout()


    def test_view_url_exists_at_proper_location(self):
        """ Tests whether page is properly loaded. """        
        response = client.get("/following")
        self.assertEqual(response.status_code, 200)


    def test_view_url_by_name(self):
        """ Tests whether page is accessible by name. """
        response = client.get(reverse('following'))
        self.assertEqual(response.status_code, 200)


    def test_view_uses_correct_template(self):
        """ Tests whether page uses correct template. """
        response = client.get(reverse('following'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'network/index.html')


    def test_view_contains_correct_html(self):
        response = client.get(reverse('following'))
        self.assertContains(response, '<div class="posts">')


    def test_view_does_not_contain_incorrect_html(self):
        response = client.get(reverse('following'))
        self.assertNotContains(response, 'This should not be on the page.')


    def test_view_url_resolves_homepageview(self):
        view = resolve('/following')
        self.assertEqual(
            view.func.__name__,
            views.following.__name__
        )


    def test_view_denied_for_non_authenticated_user(self):
        client.logout()
        response = client.get("/following")
        # Make sure status code is 302: redirect to /accounts/login/?next=/following
        self.assertEqual(response.status_code, 302)


    def test_view_pagination(self):
        """ Tests page pagination. """
        response = client.get('/following')
        
        # Request without argument: make sure 10 posts are returned in the context
        self.assertEqual(len(response.context["page_obj"]), 10)

        # Send get request to index page for page 1 and store response
        response = client.get("/following?page=1")
        # Make sure 10 posts are returned in the context
        self.assertEqual(len(response.context["page_obj"]), 10)

        # Send get request to index page for page 2 and store response
        response = client.get("/following?page=2")
        # Make sure 10 posts are returned in the context
        self.assertEqual(len(response.context["page_obj"]), 10)

        # Send get request to index page for page 3 and store response
        response = client.get("/following?page=3")
        # Make sure 5 posts are returned in the context
        self.assertEqual(len(response.context["page_obj"]), 6)



class CustomUserModelTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Create users
        u1 = User.objects.create(username='u1')
        u2 = User.objects.create(username='u2')
        u3 = User.objects.create(username='u3')

        # create posts
        p1 = Post.objects.create(created_by=u1, content='abc')
        p2 = Post.objects.create(created_by=u1, content='def')
        p3 = Post.objects.create(created_by=u2, content='ghi')

        # create follows
        u1.following.add(u2)
        u1.following.add(u3)
        u2.following.add(u1)

        # add likes
        u1.liked_posts.add(p3)
        u3.liked_posts.add(p1)
        u3.liked_posts.add(p2)
        u3.liked_posts.add(p3)


    def test_create_user(self):
        user = User.objects.create_user(
            username='adam',
            email='adam@email.com',
            password='pwd123'
        )
        self.assertEqual(user.username, 'adam')
        self.assertEqual(user.email, 'adam@email.com')
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)


    def test_create_superuser(self):
        admin_user = User.objects.create_superuser(
            username='superadmin',
            email='superadmin@email.com',
            password='test123'
        )
        self.assertEqual(admin_user.username, 'superadmin')
        self.assertEqual(admin_user.email, 'superadmin@email.com')
        self.assertTrue(admin_user.is_active)
        self.assertTrue(admin_user.is_staff)
        self.assertTrue(admin_user.is_superuser)


    def test_likes_count(self):
        u1 = User.objects.get(username='u1')
        u2 = User.objects.get(username='u2')
        u3 = User.objects.get(username='u3')

        self.assertEqual(u1.liked_posts.count(), 1)     
        self.assertEqual(u2.liked_posts.count(), 0)     
        self.assertEqual(u3.liked_posts.count(), 3)     


    def test_posts_count(self):
        u1 = User.objects.get(username='u1')
        u2 = User.objects.get(username='u2')
        u3 = User.objects.get(username='u3')

        self.assertEqual(Post.objects.all().count(), 3)
        self.assertEqual(u1.posts.count(), 2)
        self.assertEqual(u2.posts.count(), 1)
        self.assertEqual(u3.posts.count(), 0)


    def test_follows_count(self):
        u1 = User.objects.get(username='u1')
        u2 = User.objects.get(username='u2')
        u3 = User.objects.get(username='u3')

        self.assertEqual(u1.followed_by.count(), 1)
        self.assertEqual(u2.followed_by.count(), 1)
        self.assertEqual(u3.followed_by.count(), 1)

        self.assertEqual(u1.following.count(), 2)
        self.assertEqual(u2.following.count(), 1)
        self.assertEqual(u3.following.count(), 0)


    def test_get_posts_of_followed_people(self):
        u1 = User.objects.get(username='u1')
        u2 = User.objects.get(username='u2')
        u3 = User.objects.get(username='u3')

        p1 = Post.objects.get(pk=1)
        p2 = Post.objects.get(pk=2)
        p3 = Post.objects.get(pk=3)

        posts1 = u1.get_posts_of_followed_people()
        self.assertEqual(len(posts1), 1)
        self.assertIn(p3, posts1)
        
        posts2 = u2.get_posts_of_followed_people()
        self.assertEqual(len(posts2), 2)

        self.assertIn(p1, posts2)
        self.assertIn(p2, posts2)
        
        posts3 = u3.get_posts_of_followed_people()
        self.assertEqual(len(posts3), 0)



class PostModelTestCase(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Create users
        u1 = User.objects.create(username='u1')
        u2 = User.objects.create(username='u2')
        u3 = User.objects.create(username='u3')

        # create posts
        p1 = Post.objects.create(created_by=u1, content='abc')
        p2 = Post.objects.create(created_by=u1, content='def')
        p3 = Post.objects.create(created_by=u2, content='ghi')

        # add likes
        u1.liked_posts.add(p3)
        u3.liked_posts.add(p1)
        u3.liked_posts.add(p2)
        u3.liked_posts.add(p3)


    def test_text_content(self):
        p1 = Post.objects.get(id=1)
        p2 = Post.objects.get(id=2)
        p3 = Post.objects.get(id=3)
        
        content1 = f'{p1.content}'
        content2 = f'{p2.content}'
        content3 = f'{p3.content}'
        
        self.assertEqual(content1, 'abc')
        self.assertEqual(content2, 'def')
        self.assertEqual(content3, 'ghi')


    def test_likes_count(self):

        p1 = Post.objects.get(id=1)
        p2 = Post.objects.get(id=2)
        p3 = Post.objects.get(id=3)  
        
        self.assertEqual(p1.liked_by.count(), 1)     
        self.assertEqual(p2.liked_by.count(), 1)     
        self.assertEqual(p3.liked_by.count(), 2)     


    def test_get_all_posts(self):

        p1 = Post.objects.get(pk=1)
        p2 = Post.objects.get(pk=2)
        p3 = Post.objects.get(pk=3)

        all_posts = Post.get_all_posts()

        self.assertEqual(len(all_posts), 3)
        self.assertIn(p1, all_posts)
        self.assertIn(p2, all_posts)
        self.assertIn(p3, all_posts)



class PostAPITestCase(TestCase):
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Create user
        u1 = User.objects.create(username='u1')
        u2 = User.objects.create(username='u2')

        # create posts
        p1 = Post.objects.create(
            created_by=u1,
            content='abc'
        )
        p2 = Post.objects.create(created_by=u2)

        # add likes
        p1.liked_by.add(u2)

        # Create PUT payloads
        cls.payload_change_content = {
            'post_content': 'def',
        }
        cls.payload_like = {
            'liking': True,
        }
        cls.payload_unlike = {
            'liking': False,
        }


    def setUp(self):
        # log in user 1
        u1 = User.objects.get(pk=1)
        client.force_login(u1)


    def tearDown(self):
        client.logout()


    def test_get_existing_post(self):

        p1 = Post.objects.get(pk=1)
        u2 = User.objects.get(pk=2)

        response = client.get(reverse('post', kwargs={'post_id': p1.id}))
        data = response.json()
        self.assertEqual(data['id'], 1)
        self.assertEqual(data['content'], 'abc')
        self.assertEqual(data['liked_by'], [u2.id])
        self.assertEqual(response.status_code, 200)


    def test_get_nonexisting_post_raises_error(self):

        response = client.get(reverse('post', kwargs={'post_id': 99}))
        data = response.json()
        self.assertEqual(data['error'], "Post not found.")
        self.assertEqual(response.status_code, 404)


    def test_change_post_content(self):

        p1 = Post.objects.get(pk=1)

        # test content before request
        self.assertEqual(p1.content, 'abc')

        # put request
        response = client.put(
            reverse('post', kwargs={'post_id': p1.id}),
            data=json.dumps(self.payload_change_content),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 204)
        
        # test content after request     
        p1 = Post.objects.get(pk=1)   
        self.assertEqual(p1.content, 'def')


    def test_like_unlike(self):
        p2 = Post.objects.get(pk=2)
        u1 = User.objects.get(username='u1')

        # test initial status
        self.assertEqual(list(p2.liked_by.all()), [])

        # like
        response = client.put(
            reverse('post', kwargs={'post_id': p2.id}),
            data=json.dumps(self.payload_like),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 204)
        p2 = Post.objects.get(pk=2)
        self.assertEqual(list(p2.liked_by.all()), [u1])

        # like again
        response = client.put(
            reverse('post', kwargs={'post_id': p2.id}),
            data=json.dumps(self.payload_like),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 204)
        p2 = Post.objects.get(pk=2)
        self.assertEqual(list(p2.liked_by.all()), [u1])

        # unlike
        response = client.put(
            reverse('post', kwargs={'post_id': p2.id}),
            data=json.dumps(self.payload_unlike),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 204)
        p2 = Post.objects.get(pk=2)
        self.assertEqual(list(p2.liked_by.all()), [])

        # unlike again
        response = client.put(
            reverse('post', kwargs={'post_id': p2.id}),
            data=json.dumps(self.payload_unlike),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 204)
        p2 = Post.objects.get(pk=2)
        self.assertEqual(list(p2.liked_by.all()), [])


    def test_post_method_raises_error(self):

        p1 = Post.objects.get(pk=1)

        # put request
        response = client.post(
            reverse('post', kwargs={'post_id': p1.id}),
            data=json.dumps(self.payload_change_content),
            content_type='application/json'
        )
        data = response.json()
        self.assertEqual(data['error'], "GET or PUT request required.")
        self.assertEqual(response.status_code, 400)


    def test_request_denied_for_non_authenticated_user(self):
        client.logout()
        
        p1 = Post.objects.get(pk=1)

        # put request
        response = client.put(
            reverse('post', kwargs={'post_id': p1.id}),
            data=json.dumps(self.payload_change_content),
            content_type='application/json'
        )

        # Make sure status code is 302: redirect to /accounts/login/?next=/following
        self.assertEqual(response.status_code, 302)


class CreatePostAPITestCase(TestCase):
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Create user
        u1 = User.objects.create(username='u1')

        # Create payloads
        cls.valid_payload = {
            'post_content': 'Test',
        }
        cls.invalid_payload = {
            'post_content': '',
        }


    def setUp(self):
        # log in user 1
        u1 = User.objects.get(pk=1)
        client.force_login(u1)


    def tearDown(self):
        client.logout()


    def test_create_valid_post(self):        
        response = client.post(
            reverse('posts'),
            data=json.dumps(self.valid_payload),
            content_type='application/json'
        )
        data = response.json()
        self.assertEqual(data['message'], "Post created successfully.")
        self.assertEqual(response.status_code, 201)


    def test_create_invalid_post(self):        
        response = client.post(
            reverse('posts'),
            data=json.dumps(self.invalid_payload),
            content_type='application/json'
        )
        data = response.json()
        self.assertEqual(data['error'], "At least one character required.")
        self.assertEqual(response.status_code, 400)


    def test_get_method_raises_error(self):
        response = client.get(reverse('posts'))
        data = response.json()
        self.assertEqual(data['error'], "POST request required.")
        self.assertEqual(response.status_code, 400)


    def test_put_method_raises_error(self):
        response = client.put(
            reverse('posts'),
            data=json.dumps(self.valid_payload),
            content_type='application/json'
        )
        data = response.json()
        self.assertEqual(data['error'], "POST request required.")
        self.assertEqual(response.status_code, 400)


    def test_request_denied_for_non_authenticated_user(self):
        client.logout()

        # post request
        response = client.post(
            reverse('posts'),
            data=json.dumps(self.valid_payload),
            content_type='application/json'
        )

        # Make sure status code is 302: redirect to /accounts/login/?next=/following
        self.assertEqual(response.status_code, 302)



class FollowAPITestCase(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()    

        # Create users
        u1 = User.objects.create(username='u1')
        u2 = User.objects.create(username='u2')

        # Create PUT payloads
        cls.payload_follow = {
            'isfollowing': True,
        }
        cls.payload_unfollow = {
            'isfollowing': False,
        }


    def setUp(self):
        # log in user 1
        u1 = User.objects.get(pk=1)
        client.force_login(u1)


    def tearDown(self):
        client.logout()


    def test_get_status(self):

        u1 = User.objects.get(username='u1')
        u2 = User.objects.get(username='u2')

        # test initial status --> not following
        response = client.get(reverse('follow', kwargs={'user_id': u2.id}))
        data = response.json()
        self.assertFalse(data['isfollowing'])
        self.assertEqual(response.status_code, 200)
        # make u1 follow u2
        u1.follow(u2)
        response = client.get(reverse('follow', kwargs={'user_id': u2.id}))
        data = response.json()
        self.assertTrue(data['isfollowing'])
        self.assertEqual(response.status_code, 200)        


    def test_toggle_status(self):

        u1 = User.objects.get(username='u1')
        u2 = User.objects.get(username='u2')

        # reset follow status
        u1.unfollow(u2)
        self.assertFalse(u1.is_following(u2))

        # follow
        response = client.put(
            reverse('follow', kwargs={'user_id': u2.id}),
            data=json.dumps(self.payload_follow),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 204)
        self.assertTrue(u1.is_following(u2))

        # follow again
        response = client.put(
            reverse('follow', kwargs={'user_id': u2.id}),
            data=json.dumps(self.payload_follow),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 204)
        self.assertTrue(u1.is_following(u2))

        # unfollow
        response = client.put(
            reverse('follow', kwargs={'user_id': u2.id}),
            data=json.dumps(self.payload_unfollow),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 204)
        self.assertFalse(u1.is_following(u2))

        # unfollow again
        response = client.put(
            reverse('follow', kwargs={'user_id': u2.id}),
            data=json.dumps(self.payload_unfollow),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 204)
        self.assertFalse(u1.is_following(u2))


    def test_post_method_raises_error(self):

        u1 = User.objects.get(username='u1')
        u2 = User.objects.get(username='u2')

        response = client.post(
            reverse('follow', kwargs={'user_id': u2.id}),
            data=json.dumps(self.payload_follow),
            content_type='application/json'
        )
        data = response.json()
        self.assertEqual(data['error'], "GET or PUT request required.")
        self.assertEqual(response.status_code, 400)


    def test_get_status_for_invalid_user_raises_error(self):

        response = client.get(reverse('follow', kwargs={'user_id': 3}))
        data = response.json()
        self.assertEqual(data['error'], "User not found.")
        self.assertEqual(response.status_code, 404)


    def test_toggle_status_for_invalid_user_raises_error(self):

        response = client.put(
            reverse('follow', kwargs={'user_id': 3}),
            data=json.dumps(self.payload_follow),
            content_type='application/json'
        )
        data = response.json()
        self.assertEqual(data['error'], "User not found.")
        self.assertEqual(response.status_code, 404)



class ControlsTestCaseLoggedIn(LiveServerTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Create users
        u1 = User.objects.create(username='u1')        
        # create  posts
        for _ in range(25):
            Post.objects.create(created_by=u1)

        cls.selenium = webdriver.Chrome(R"c:\Users\Judit\Documents\Qsync\CS50 Web\cs50web\Lib\site-packages\chromedriver_py\chromedriver_win32.exe")

        client.force_login(u1)
        session_key = client.cookies[settings.SESSION_COOKIE_NAME].value
        cls.selenium.get(f'{cls.live_server_url}')
        cls.selenium.add_cookie({'name': settings.SESSION_COOKIE_NAME, 'value': session_key, 'path': '/'})
        cls.selenium.refresh()


    @classmethod
    def tearDownClass(cls):
        cls.selenium.quit()
        super().tearDownClass()


    def test_index_page_contains_create_post_button(self):
        self.selenium.get(f'{self.live_server_url}')
        new_post_button = self.selenium.find_element_by_id("btn-create-post")
        self.assertEqual(new_post_button.text,'Create new post')


    def test_following_page_contains_create_post_button(self):
        self.selenium.get(f'{self.live_server_url}/following')
        new_post_button = self.selenium.find_element_by_id("btn-create-post")
        self.assertEqual(new_post_button.text,'Create new post')



class ControlsTestCaseLoggedOut(LiveServerTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Create users
        u1 = User.objects.create(username='u1')        
        # create  posts
        for _ in range(25):
            Post.objects.create(created_by=u1)

        cls.selenium = webdriver.Chrome(R"c:\Users\Judit\Documents\Qsync\CS50 Web\cs50web\Lib\site-packages\chromedriver_py\chromedriver_win32.exe")


    @classmethod
    def tearDownClass(cls):
        cls.selenium.refresh()
        cls.selenium.quit()
        super().tearDownClass()

    def test_index_page_does_not_contain_create_post_button(self):
        self.selenium.get(f'{self.live_server_url}')
        with self.assertRaises(NoSuchElementException):
            new_post_button = self.selenium.find_element_by_id("btn-create-post")


###########  NOTES  ###########

# https://realpython.com/test-driven-development-of-a-django-restful-api/