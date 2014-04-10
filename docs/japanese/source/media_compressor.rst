
======================
メディア圧縮機能を使う
======================

.. note::

   この機能はまだ実験段階です。将来仕様が変わる可能性があります。

概要
========

もし、あなたのアプリケーションで多くのjavascriptおよびcssファイルを使っているなら、
それらのファイルの読み込みにそれなりのコストがかかるでしょう。
ウェブページの読み込みの際のコストを減らしたいのであれば、 ``media compressor`` を使うとよいでしょう。

Kayのデフォルトでは, バンドルしているjsminのモジュールをjavascriptの圧縮に使います。
cssについては、結合アルゴリズム(文字通り、すべてのcssを順番に結合するだけ）を使います。

javascriptおよびcssの圧縮に使うツールは、それぞれ個別に変更することが可能です。

圧縮されたファイルはデフォルトでは、 ``_generated_media`` ディレクトリに保存されます。 
このディレクトリを、app.yamlの設定に、静的ファイルを扱うディレクトリとして登録する必要があります。


メディア圧縮　クイックスタート
=====================================

メディア圧縮機能を使うには,  ``CONTEXT_PROCESSORS`` の変数に、context_processorを追加する必要があります。
設定する変数は2種類あります。

開発中のアプリケーションが以下のようなmediaディレクトリ構造を持っているとしましょう:

.. code-block:: bash

   $ tree media
   media
   |-- css
   |   |-- base_layout.css
   |   |-- common.css
   |   |-- component.css
   |   |-- fonts.css
   |   |-- subpages.css
   |   `-- toppage.css
   |-- images
   `-- js
       |-- base.js
       |-- jquery-ui.min.js
       |-- jquery.min.js
       |-- subpage.js
       `-- toppage.js

トップページではbase.jsとtoppage.js、そしてsubpages.cssを除くすべてのcssファイルを使っているとします。
また、個別ページではbase.jsとsubpage.js、toppage.cssを除くすべてのcssファイルを使っているとします。

以下がその場合の単純な設定方法です:

settings.py:

.. code-block:: python

   CONTEXT_PROCESSORS = (
     'kay.context_processors.request',
     'kay.context_processors.url_functions',
     'kay.context_processors.media_url',
     'kay.ext.media_compressor.context_processors.media_urls',
   )

   COMPILE_MEDIA_JS = {
     'toppage.js': {
       'output_filename': 'toppage.js',
       'source_files': (
	 'media/js/jquery.min.js',
	 'media/js/jquery-ui.min.js',
	 'media/js/base.js',
	 'media/js/toppage.js',
       ),
     },
     'subpages.js': {
       'output_filename': 'subpages.js',
       'source_files': (
	 'media/js/base.js',
	 'media/js/subpage.js',
       ),
     },
   }

   COMPILE_MEDIA_CSS = {
     'toppage.css': {
       'output_filename': 'toppage.css',
       'source_files': (
	 'media/css/common.css',
	 'media/css/component.css',
	 'media/css/fonts.css',
	 'media/css/base_layout.css',
	 'media/css/toppage.css',
       ),
     },
     'subpages.css': {
       'output_filename': 'subpages.css',
       'source_files': (
	 'media/css/common.css',
	 'media/css/component.css',
	 'media/css/fonts.css',
	 'media/css/base_layout.css',
	 'media/css/subpages.css',
       ),
     },
   }

yourapp/templates/index.html:

.. code-block:: html

   <!DOCTYPE html>
   <html>
   <head>
   <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
   <title>Top Page</title>
   {{ compiled_css('toppage.css') }}
   {{ compiled_js('toppage.js') }}
   </head>
   <body>
   Your html goes here
   </body>
   </html>

開発サーバーでは、圧縮はデフォルトでは無効になっています。
そのため、ここにあるcompiled_*** という部分は、以下のように展開されます。:

.. code-block:: html

   <link type="text/css" rel="stylesheet" href="/media/css/common.css" /> 
   <link type="text/css" rel="stylesheet" href="/media/css/component.css" /> 
   <link type="text/css" rel="stylesheet" href="/media/css/fonts.css" /> 
   <link type="text/css" rel="stylesheet" href="/media/css/base_layout.css" /> 
   <link type="text/css" rel="stylesheet" href="/media/css/toppage.css" /> 

   <script type="text/javascript" src="media/js/jquery.min.js"></script> 
   <script type="text/javascript" src="media/js/jquery-ui.min.js"></script> 
   <script type="text/javascript" src="media/js/base.js"></script> 
   <script type="text/javascript" src="media/js/toppage.js"></script> 


これらのファイルをコンパイルして圧縮するには、``manage.py``に``compile_media``の
サブコマンドを指定して実行します。

.. code-block:: bash

   $ python manage.py compile_media
   Running on Kay-0.8.0
   Compiling css media [toppage.css]
    concat /Users/tmatsuo/work/mediatest/media/css/common.css
    concat /Users/tmatsuo/work/mediatest/media/css/component.css
    concat /Users/tmatsuo/work/mediatest/media/css/fonts.css
    concat /Users/tmatsuo/work/mediatest/media/css/base_layout.css
    concat /Users/tmatsuo/work/mediatest/media/css/toppage.css
   Compiling css media [subpages.css]
    concat /Users/tmatsuo/work/mediatest/media/css/common.css
    concat /Users/tmatsuo/work/mediatest/media/css/component.css
    concat /Users/tmatsuo/work/mediatest/media/css/fonts.css
    concat /Users/tmatsuo/work/mediatest/media/css/base_layout.css
    concat /Users/tmatsuo/work/mediatest/media/css/subpages.css
   Compiling js media [toppage.js]
   Compiling js media [subpages.js]

   $ tree _generated_media

   _generated_media
   `-- 1
       |-- css
       |   |-- subpages.css
       |   `-- toppage.css
       `-- js
	   |-- subpages.js
	   `-- toppage.js

   3 directories, 4 files

これらのファイルを使えるようにするにはapp.yamlの設定に
このディレクトリを追加する必要があります。
(Kayのバージョンによっては、最初から設定されている場合があります）以下のように設定します。:

.. code-block:: yaml

   - url: /_generated_media
     static_dir: _generated_media

これで、圧縮されたファイルをデプロイする準備ができました。
この例に挙げたケースでは、実際にアクセスして際に提供されるHTMLは以下のようになります。:

.. code-block:: html

   <!DOCTYPE html>
   <html> 
   <head> 
   <meta http-equiv="Content-Type" content="text/html; charset=UTF-8"> 
   <title>Top Page - myapp</title> 
   <link type="text/css" rel="stylesheet" href="/_generated_media/1/css/toppage.css" /> 

   <script type="text/javascript" src="/_generated_media/1/js/toppage.js"></script> 

   </head> 
   <body> 
   Your contents go here.
   </body> 
   </html>

リファレンス
================

javascriptの圧縮の際に使用可能なオプション:

* ``concat``

  単純にjavascriptsをつなげて結合します。

* ``jsminify``

  javascriptsの圧縮の際にバンドルしているjsminモジュールを使います。

* ``goog_calcdeps``

  グーグルのclosure libraryにあるcalcdeps.pyを圧縮および依存関係の計算に使います。

* ``goog_compiler``

  jsファイルの圧縮にclosure compilerを使います。


cssの圧縮の際に使用可能なオプション:

* ``separate``

  すべてのcssファイルをコピーします。

* ``concat``

  単純にすべてのcssファイルをつないで結合します。

* ``csstidy``

  圧縮の際にcsstidyを使います。あらかじめ、自分の環境にcsstidyをインストールしておく必要があります。


TODO
====

* 画像への対応
* より詳細なリファレンス


