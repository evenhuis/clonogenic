from ipywidgets import Dropdown, Text, Select, Button, HTML
from ipywidgets import Layout, GridBox, HBox, VBox
from utils import update_path, get_subpaths, get_dir_contents
import os

def check_path(path):
	import glob
	pathOK = False
	exp_files=glob.glob(path+"/*context*.xls")
	if( len(exp_files)>0 ):
		context_file = exp_files[0]
		excel_file   = context_file.replace("Exp_context","DataTable")
		if( os.path.isfile(os.path.join(path,excel_file) ) ):
			pathOK = True
	return pathOK


def check_plate_path( path ):
	''' Checks if each child direcotry in this path  as a DataTable and Exp_context '''
	dirs = [ f for f in os.listdir(path) if os.path.isdir(os.path.join(path,f))  ]
	stats = [ check_path(os.path.join(path,d)) for d in dirs ]
	return all( stats )
		


class FileChooser(VBox):

	_LBL_TEMPLATE = '<span style="margin-left:10px; color:{1};">{0}</span>'
	_LBL_NOFILE = 'No file selected'

	def __init__(
			self,
			path=os.getcwd(),
			filename='',
			title='',
			select_desc='Select',
			change_desc='Change',
			show_hidden=False,
			directory=False,
			**kwargs):

		self._select_desc=select_desc
		self._default_path = path
		self._show_hidden = show_hidden
		self._select_desc = select_desc
		self._change_desc = change_desc
		self._path = path


		self._updir = Button(description='Up Directory')


		self._dircontent = Select(
			rows=8,
			layout=Layout(
				width='auto',
				grid_area='dircontent'
			)
		)
		self._cancel = Button(
			description='Cancel',
			layout=Layout(
				width='auto',
				display='none'
			)
		)
		self._select = Button(
			description=self._select_desc,
			layout=Layout(width='auto')
		)

		self._label = HTML(
			value=self._LBL_TEMPLATE.format(
				self._LBL_NOFILE,
				'black'
			),
			placeholder='',
			description=''
		)

		self._title = HTML(
			value=title
		)

		if title is '':
			self._title.layout.display = 'none'

		self._updir.on_click(self._on_updir_click)
		self._select.on_click(self._on_select_click)
		self._cancel.on_click(self._on_cancel_click)


		# Layout
		self._gb = GridBox(
			children=[
				self._updir,
				self._dircontent
			],
			layout=Layout(
				display='none',
				width='500px',
				grid_gap='0px 0px',
				grid_template_rows='auto auto',
				grid_template_columns='60% 40%',
				grid_template_areas='''
					'pathlist filename'
					'dircontent dircontent'
					'''
			)
		)



		self._dircontent.observe(
			self._on_dircontent_select,
			names='value'
		)

		buttonbar = HBox(
			children=[
				self._select,
				self._cancel,
				self._label,
			],
			layout=Layout(width='auto')
		)

		# Call setter to set initial form values
		self._set_form_values(
			self._path
		)

		# Call VBox super class __init__
		super().__init__(
			children=[
				self._gb,
				buttonbar,
			],
			layout=Layout(width='auto'),
			**kwargs
		)

	def _set_form_values(self,path ):
		# Disable triggers to prevent selecting an entry in the Select
		# box from automatically triggering a new event.
		self._dircontent.unobserve(
			self._on_dircontent_select,
			names='value'
		)		

		self._dircontent.options = get_dir_contents(
			path,
			hidden=self._show_hidden
		)
		self._dircontent.value = None

		# Reenable triggers again
		self._dircontent.observe(
			self._on_dircontent_select,
			names='value'
		)

	def _on_dircontent_select(self, change):
		'''Handler for when a folder entry is selected'''
		new_path = update_path(
			self._path,
			change['new']
		)

		# Check if folder or file
		if os.path.isdir(new_path):
			self._path = new_path
		#elif os.path.isfile(new_path):
		#	path = self._path

		self._set_form_values(
			self._path
		)

	def _on_updir_click(self, b):
		self._path = os.path.split(self._path)[0]
		self._set_form_values(self._path )

	def _on_cancel_click(self, b):
		self._gb.layout.display = 'none'

	def _on_select_click(self, b):
		'''Handler for when the select button is clicked'''
		if self._gb.layout.display is 'none':
			self._gb.layout.display = None
			self._cancel.layout.display = None
			
			path = self._default_path
			self._set_form_values(path )

		else:
			self._gb.layout.display = 'none'
			self._cancel.layout.display = 'none'
			self._select.description = self._change_desc
			#self._selected_filename = self._filename.value
			# self._default_path = self._selected_path
			# self._default_filename = self._selected_filename

			selected_path = self._path
			#if( os.path.isdir( selected_path ) ):
			#	self._path = selected_path
	
			pathOK = check_plate_path( self._path )	
			color = 'red'
			if( pathOK ): color ='green'
			self._label.value = self._LBL_TEMPLATE.format(
				selected_path,
				color
			)
			self._set_form_values(
				self._path
			)
			
